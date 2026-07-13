"""Incumbent hand-written validator for a `create_user` tool.

This is *untrusted third-party code* (someone's existing hand-written tool
validator) -- the schema-lift loop runs it only inside the sandbox.  The loop
has the LLM infer a JSON Schema from it, then certifies the inferred schema by
differential against this validator: this code is the free ground-truth
anchor.

Contract it enforces: required username(str), age(int), role in {admin,user};
optional email(str); no extra keys; bool is not accepted for age.
"""


def accepts(data):
    if not isinstance(data, dict):
        return False
    allowed = {"username", "age", "email", "role"}
    if set(data.keys()) - allowed:
        return False
    if "username" not in data or type(data["username"]) is not str:
        return False
    if "age" not in data or type(data["age"]) is not int:
        return False
    if "role" not in data or data["role"] not in ("admin", "user"):
        return False
    if "email" in data and type(data["email"]) is not str:
        return False
    return True
