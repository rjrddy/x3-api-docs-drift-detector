"""Compare documented contracts with a running app's OpenAPI and observed HTTP traffic."""

import argparse
import json
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel


class Item(BaseModel):
    id: int
    name: str


def create_app() -> FastAPI:
    app = FastAPI()
    for i in range(10):

        def endpoint(item_id: int) -> dict:
            return {"id": item_id, "name": f"Synthetic item {item_id}"}

        app.add_api_route(
            f"/items{i}/{{item_id}}", endpoint, response_model=Item, operation_id=f"get_item_{i}"
        )
    return app


def schema(spec: dict, operation: dict) -> dict:
    value = operation["responses"]["200"]["content"]["application/json"]["schema"]
    return (
        spec["components"]["schemas"][value["$ref"].rsplit("/", 1)[1]] if "$ref" in value else value
    )


def document(spec: dict, traffic: list[dict]) -> list[dict]:
    docs = []
    for sample in traffic:
        path = sample["template"]
        operation = spec["paths"][path]["get"]
        shape = schema(spec, operation)
        docs.append(
            {
                "path": path,
                "method": "get",
                "operation_id": operation["operationId"],
                "parameter_type": operation["parameters"][0]["schema"]["type"],
                "parameter_required": operation["parameters"][0]["required"],
                "fields": {k: v["type"] for k, v in shape["properties"].items()},
                "required_fields": shape["required"],
                "response_status": 200,
                "example": sample["response"],
            }
        )
    return docs


def detect(docs: list[dict], spec: dict, traffic: list[dict]) -> list[dict]:
    findings = []
    for doc in docs:
        path = doc["path"]
        reason = None
        if path not in spec["paths"]:
            reason = "documented path missing from live spec"
        elif doc["method"] not in spec["paths"][path]:
            reason = "documented method missing from live spec"
        else:
            operation = spec["paths"][path][doc["method"]]
            shape = schema(spec, operation)
            if doc["operation_id"] != operation["operationId"]:
                reason = "operation ID drift"
            elif doc["parameter_type"] != operation["parameters"][0]["schema"]["type"]:
                reason = "parameter type drift"
            elif doc["parameter_required"] != operation["parameters"][0]["required"]:
                reason = "parameter requiredness drift"
            elif doc["fields"] != {k: v["type"] for k, v in shape["properties"].items()}:
                reason = "response field shape drift"
            elif str(doc["response_status"]) not in operation["responses"]:
                reason = "response status drift"
            elif set(doc["required_fields"]) != set(shape["required"]):
                reason = "required response fields drift"
            else:
                actual = next(r["response"] for r in traffic if r["template"] == path)
                if any(type(doc["example"].get(k)) is not type(v) for k, v in actual.items()):
                    reason = "documented example type disagrees with observed traffic"
        if reason:
            findings.append({"path": path, "reason": reason})
    return findings


def fixtures() -> tuple[list[dict], dict, list[dict], list[dict]]:
    with TestClient(create_app()) as client:
        spec = client.get("/openapi.json").json()
        traffic = []
        for i in range(10):
            response = client.get(f"/items{i}/{i}")
            response.raise_for_status()
            traffic.append(
                {
                    "template": f"/items{i}/{{item_id}}",
                    "url": f"/items{i}/{i}",
                    "status": response.status_code,
                    "response": response.json(),
                }
            )
    clean = document(spec, traffic)
    bad = json.loads(json.dumps(clean))
    bad[0]["path"] = "/obsolete"
    bad[1]["method"] = "post"
    bad[2]["operation_id"] = "old_name"
    bad[3]["parameter_type"] = "string"
    bad[4]["parameter_required"] = False
    bad[5]["fields"].pop("name")
    bad[6]["fields"]["id"] = "string"
    bad[7]["response_status"] = 201
    bad[8]["required_fields"] = []
    bad[9]["example"]["id"] = "wrong-type"
    return clean, spec, traffic, bad


def benchmark() -> dict:
    clean, spec, traffic, bad = fixtures()
    findings = detect(bad, spec, traffic)
    controls = detect(clean, spec, traffic)
    assert len(findings) == 10 and not controls
    Path("evidence/live-openapi.json").write_text(json.dumps(spec, indent=2))
    Path("evidence/traffic.json").write_text(json.dumps(traffic, indent=2))
    Path("evidence/findings.json").write_text(json.dumps(findings, indent=2))
    Path("evidence/drifted-docs.json").write_text(json.dumps(bad, indent=2))
    Path("evidence/proposed-docs.json").write_text(json.dumps(clean, indent=2))
    return {
        "seeded_drifts": len(bad),
        "drifts_detected": len(findings),
        "clean_contract_false_positives": len(controls),
        "observed_http_requests": len(traffic),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-docs", type=Path)
    args = parser.parse_args()
    if args.check_docs:
        _, live_spec, observed, _ = fixtures()
        findings = detect(json.loads(args.check_docs.read_text()), live_spec, observed)
        print(json.dumps(findings, indent=2))
        raise SystemExit(1 if findings else 0)
    print(json.dumps(benchmark(), indent=2))
