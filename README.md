# Flask-Hammer

_"Flask-Hammer - For when every problem looks like a nail."_

* You probably don't need this. There are better ways to do what this does.
* It wraps up Flask, Gunicorn and some bundled functionality to make a "batteries-included" Flask setup

Flask is excellent and requires very little boilerplate to get started; but I find myself writing many Flask apps with very similar structures and the same basic components with too much copy-pasting on my part for things like Metrics, Traces, Middleware, Responses, etc.

This lib is my kludgy way to reduce the boilerplate of those added extras that I so often rely on when deploying micro services or small apps in k8s.

Flask-Hammer's value (to me) is in helping to stand up a batteries-included flask app very quickly from an idea or for an MVP.
Its value to anyone else is probably minimal.

Contributions and fixes are welcome, but for the time being this is deliberately more of an idiosyncratic convenience library than anything else.


# PyPi
https://pypi.org/project/kv-flask-hammer/

# Installation
### With Poetry:
`poetry add kv-flask-hammer`

### With pip:
`pip install kv-flask-hammer`


# Example Usage

```python
from kv_flask_hammer import FlaskHammer

def example_periodic_job():
    print("Job Tick!")

app = FlaskHammer()

# Almost all of these config changes are optional
# Defaults can be found in constants.py

# For SSL
app.config.flask_set_secret_key("test")

# Set bind IP address and port for gunicorn/flask
app.config.set_ip_port("0.0.0.0", "5000")

# Enable Middleware and add a class
app.config.middleware_enable()
app.config.middleware_set_cls(ExampleMiddlewareClass)

# Enable basic healthz/livez routes
app.config.healthz_view_enable()

# Enable 'meta' view with routes for debugging
app.config.meta_view_enable()

# Enable prometheus metrics and expose them on a given port
app.config.metrics_enable()
app.config.metrics_set_ip_port("0.0.0.0", 9090)

# Enable OTLP Traces
app.config.traces_enable()

# Enable periodic jobs
app.config.jobs_enable()
# We can add jobs that run on periodic intervals (using Flask-APScheduler under the hood)
app.add_periodic_job(job_func=example_periodic_job, job_id="example_job_1", interval_seconds=5)

# Flask App object is accessible here for mutating the app in other ways or passing it around, etc.
flask_app = app.flask_app

def main():
    return app.run_with_gunicorn()
```

### Starting the above example app from e.g.; a bash script as a Docker Container entrypoint:
```bash
.venv/bin/python -c "from flask_hammer_example import main; main()"
```

## Why 'kv_'?

* I prefix most of my projects, libs, etc. with 'kv' or 'zkv' for reasons that aren't interesting to anyone else.
* This library isn't purporting or pretending to be in any way official or associated with Flask; nor is it a plugin for it. It'd feel weird to just call it `flask-hammer` officially (and on pypi, etc.) in light of that.

## Notice

This library is not associated with Flask, Gunicorn or their maintainers or contributors. It's just a convenience library made independently for my own use.