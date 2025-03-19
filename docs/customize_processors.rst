Customize Content Processors
============================

.. code-block::
    :caption: settings.py

    OASIS_REQUEST_COPNTENT_PROCESSORS = {
        "application/yaml": "<your-project>.processors.yaml_request_processor"
    }

    OASIS_RESPONSE_CONTENT_PROCESSORS = {
        "application/yaml": "<your-project>.processors.yaml_response_processor"
    }

.. literalinclude:: /_samples/customize_processors/processors.py
    :caption: processors.py

.. literalinclude:: /_samples/customize_processors/views.py

.. swaggerui:: _samples.customize_processors.urls.router
