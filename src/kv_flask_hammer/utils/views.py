from flask import jsonify
from flask import Response


def get_url_map() -> Response:
    from flask import current_app as app

    url_map = app.url_map
    rules_dict = dict()
    for rule in url_map.iter_rules():
        rule_dict = dict()
        rule_dict["route"] = rule.rule
        rule_dict["methods"] = str(rule.methods)
        rules_dict[rule.endpoint] = rule_dict
    return jsonify(rules_dict)
