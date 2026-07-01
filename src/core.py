import os
import re
import json
import time
import random
import logging
import pandas as pd
import tiktoken

from typing import Optional, Literal
from pydantic import BaseModel

from openai import AzureOpenAI, RateLimitError, OpenAIError
from azure.core.credentials import AzureKeyCredential

try:
    from azure.ai.inference import ChatCompletionsClient
    from azure.ai.inference.models import SystemMessage, UserMessage, JsonSchemaFormat
    HAS_AZURE_INFERENCE = True
except ImportError:
    HAS_AZURE_INFERENCE = False

try:
    from json_repair import repair_json
    HAS_JSON_REPAIR = True
except ImportError:
    HAS_JSON_REPAIR = False


# =========================
# SCHEMA
# =========================

class FHx_Object(BaseModel):
    reasoning: str
    FamilyMember: Optional[str] = None
    AgeofOnset: Optional[int] = None
    Observation: Optional[str] = None
    SideoftheFamily: Optional[Literal["Maternal", "Paternal", "Unknown"]] = None
    LivingStatus: Optional[Literal["Alive", "Dead", "Unknown"]] = None
    Age: Optional[int] = None
    AgeofDeath: Optional[int] = None
    CauseofDeath: Optional[bool] = None
    CUI: Optional[str] = None
    Negated: Optional[bool] = None


class FamilyHistory(BaseModel):
    full_history: list[FHx_Object]


JSON_SCHEMA = FamilyHistory.model_json_schema()


# =========================
# PARSING
# =========================

def manual_json_repair(text: str) -> str:
    text = text.strip()
    text = re.sub(r'^```json\s*\n?', '', text)
    text = re.sub(r'^```\s*\n?', '', text)
    text = re.sub(r'\n?```$', '', text)
    text = re.sub(r',(\s*[}\]])', r'\1', text)
    text = re.sub(r':\s*None\b', ': null', text)
    text = re.sub(r':\s*True\b', ': true', text)
    text = re.sub(r':\s*False\b', ': false', text)
    text = re.sub(r"{\s*'", '{"', text)
    text = re.sub(r"'\s*:", '":', text)
    text = re.sub(r":\s*'([^']*)'(\s*[,}])", r': "\1"\2', text)
    text = re.sub(r'{\s*(\w+)\s*:', r'{"\1":', text)
    text = re.sub(r',\s*(\w+)\s*:', r', "\1":', text)
    return text.strip()


def parse_response(response_content: str, doc_id: str = "unknown") -> dict:
    if not response_content or not response_content.strip():
        return {"error": "empty_response", "full_history": []}

    text = response_content.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    if HAS_JSON_REPAIR:
        try:
            return repair_json(text, return_objects=True)
        except Exception:
            pass

    try:
        return json.loads(manual_json_repair(text))
    except Exception:
        pass

    try:
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            return json.loads(manual_json_repair(match.group()))
    except Exception:
        pass

    return {
        "error": "json_parse_failed",
        "raw_response": text[:1000],
        "full_history": []
    }


# =========================
# TOKENS
# =========================

def get_tokenizer(model_name="gpt-4o"):
    return tiktoken.encoding_for_model(model_name)


def count_tokens(text: str, model_name="gpt-4o") -> int:
    tok = get_tokenizer(model_name)
    return len(tok.encode(text))


def chunk_text(text: str, max_tokens: int, model_name="gpt-4o"):
    tok = get_tokenizer(model_name)
    tok_ids = tok.encode(text)
    return [tok.decode(tok_ids[i:i + max_tokens]) for i in range(0, len(tok_ids), max_tokens)]


# =========================
# CLIENTS
# =========================

def setup_azure_openai_client(endpoint: str, api_key: str, api_version="2024-12-01-preview"):
    return AzureOpenAI(azure_endpoint=endpoint, api_key=api_key, api_version=api_version)


def setup_inference_client(endpoint: str, api_key: str):
    return ChatCompletionsClient(endpoint=endpoint, credential=AzureKeyCredential(api_key))


# =========================
# MODEL CALLS
# =========================

def call_openai_model(client, doc: str, prompt: str, model_name: str, doc_id="unknown"):
    sys_msg = {"role": "system", "content": prompt}
    user_msg = {"role": "user", "content": doc}
    resp = client.chat.completions.parse(
        model=model_name,
        messages=[sys_msg, user_msg],
        response_format=FamilyHistory
    )
    return parse_response(resp.choices[0].message.content, doc_id)


def call_inference_model(client, doc: str, prompt: str, doc_id="unknown"):
    resp = client.complete(
        response_format=JsonSchemaFormat(
            name="FHx_Schema",
            schema=JSON_SCHEMA,
            description="Extract family health history from document",
            strict=False,
        ),
        messages=[
            SystemMessage(content=prompt),
            UserMessage(content=doc),
        ],
        temperature=0,
    )
    return parse_response(resp.choices[0].message.content, doc_id)


# =========================
# BATCH
# =========================

def call_batch(
    documents_df: pd.DataFrame,
    id_col: str,
    text_col: str,
    dataset_label: str,
    prompt: str,
    backend: str,
    client,
    model_name: str = None,
    save_path: str = "_fhx",
    output_dir: str = ".",
    max_retries: int = 4,
    backoff_base: float = 2.0,
    sleep_between: float = 0.5,
    save_every: int = 20,
    max_prompt_tokens: int = 5000,
    tokenizer_model: str = "gpt-4o",
):
    records = []

    for idx, row in documents_df.iterrows():
        doc_id = row[id_col]
        full_txt = str(row[text_col])
        txt_tokens = count_tokens(full_txt, tokenizer_model)

        print(f"[{idx + 1}/{len(documents_df)}] ID={doc_id} ({txt_tokens} tokens)")

        chunks = [full_txt] if txt_tokens <= max_prompt_tokens else chunk_text(full_txt, max_prompt_tokens, tokenizer_model)

        all_parts = []

        for c_idx, chunk in enumerate(chunks, start=1):
            attempt = 0
            resp = None

            while True:
                try:
                    if backend == "openai":
                        output = call_openai_model(client, chunk, prompt, model_name, doc_id=f"{doc_id}_chunk{c_idx}")
                    elif backend == "inference":
                        output = call_inference_model(client, chunk, prompt, doc_id=f"{doc_id}_chunk{c_idx}")
                    else:
                        raise ValueError(f"Unknown backend: {backend}")

                    resp = output
                    all_parts.append(resp)
                    break

                except (RateLimitError, OpenAIError, Exception) as e:
                    attempt += 1
                    if attempt > max_retries:
                        logging.exception(f"ID={doc_id} failed after {max_retries} retries: {e}")
                        all_parts.append({"error": str(e)})
                        break

                    sleep_time = (backoff_base ** (attempt + 2)) + random.uniform(0, 1)
                    logging.warning(f"Retry {attempt}/{max_retries} for {doc_id}. Sleeping {sleep_time:.1f}s. Error: {e}")
                    time.sleep(sleep_time)

            if sleep_between and resp is not None:
                time.sleep(sleep_between)

        combined = {
            "full_history": [
                item
                for part in all_parts
                if isinstance(part, dict) and "full_history" in part
                for item in part.get("full_history", [])
            ]
        }

        records.append({
            id_col: doc_id,
            "dataset": dataset_label,
            "response": json.dumps(combined),
        })

        if save_every and len(records) % save_every == 0:
            checkpoint_path = os.path.join(output_dir, f"checkpoint_{dataset_label}_{save_path}.csv")
            pd.DataFrame(records).to_csv(checkpoint_path, index=False)

    return pd.DataFrame(records)