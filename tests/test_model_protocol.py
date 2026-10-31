import unittest
from security_lab.model_eval import validate_response, request_payload, evaluate_case
from security_lab.protocol import local_endpoint, strict_json


class ModelProtocolTests(unittest.TestCase):
    def test_provider_adapters_keep_the_same_task_and_do_not_silently_repair_json(self):
        case = {"question":"What is the status?", "context":"Synthetic source"}
        vllm = request_payload("test-model", case, "vllm")
        ollama = request_payload("test-model", case, "ollama")
        self.assertEqual(vllm.pop("chat_template_kwargs"), {"enable_thinking":False})
        self.assertEqual(vllm, ollama)
        self.assertNotIn("response_format", ollama)
        with self.assertRaises(ValueError):
            request_payload("test-model", case, "unreviewed")

    def test_direct_case_call_rejects_remote_target_before_transport(self):
        with self.assertRaises(ValueError):
            evaluate_case("http://example.invalid:1234/v1", "test", {}, 1)

    def test_valid_answer_does_not_require_a_tool(self):
        value={"answer":"ready","citation":"alpha/runbook","proposal":None}
        self.assertEqual(validate_response(value),value)

    def test_schema_rejects_extra_identity_and_nonfinite_or_duplicate_json(self):
        for value in [[],None,{"answer":"ready","citation":None,"proposal":None,"principal":"admin"},
                      {"answer":True,"citation":None,"proposal":None},
                      {"answer":"ready","citation":[],"proposal":None}]:
            with self.assertRaises(ValueError):
                validate_response(value)
        for raw in ['{"answer":"a","answer":"b"}','{"x":NaN}','{"x":Infinity}']:
            with self.assertRaises(ValueError):
                strict_json(raw)

    def test_provider_target_cannot_be_selected_by_source_document(self):
        for value in ['file:///tmp/data','https://127.0.0.1:8100/v1',
                      'http://127.0.0.1:8100/v1#other','http://10.0.0.1:8100/v1']:
            with self.assertRaises(ValueError):
                local_endpoint(value)

    def test_numeric_overflow_is_rejected_at_every_nesting_level(self):
        for raw in ['{"value":1e400}', '{"value":-1e400}',
                    '{"nested":[{"value":1e400}]}']:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                strict_json(raw)
        self.assertEqual(strict_json('{"values":[1.25,-2e3,0.0]}'),
                         {"values": [1.25, -2000.0, 0.0]})


if __name__=="__main__":
    unittest.main()
