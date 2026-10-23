import unittest
from security_lab.model_eval import validate_response
from security_lab.protocol import local_endpoint, strict_json


class ModelProtocolTests(unittest.TestCase):
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


if __name__=="__main__":
    unittest.main()
