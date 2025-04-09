Customize Content Processors
============================

.. code-block::
    :caption: settings.py

    OASIS_REQUEST_CONTENT_PROCESSORS = {
        "application/yaml": "<your-project>.processors.yaml_request_processor"
    }

    OASIS_RESPONSE_CONTENT_PROCESSORS = {
        "application/yaml": "<your-project>.processors.yaml_response_processor"
    }

.. literalinclude:: /_samples/django/customize_processors/processors.py
    :caption: processors.py

.. literalinclude:: /_samples/django/customize_processors/views.py

.. swaggerui:: _samples.django.customize_processors.urls.router
