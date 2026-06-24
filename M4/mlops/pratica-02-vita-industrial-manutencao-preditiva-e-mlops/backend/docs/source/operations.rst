Execução
========

Ambiente
--------

.. code-block:: bash

   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

API
---

.. code-block:: bash

   uvicorn backend.app:app --reload

Dashboard
---------

.. code-block:: bash

   streamlit run frontend/streamlit/app.py

MLflow
------

.. code-block:: bash

   mlflow ui --backend-store-uri sqlite:///artifacts/tracking/mlflow.db --port 5000

Testes
------

.. code-block:: bash

   pytest -q

Docker
------

.. code-block:: bash

   docker compose up --build

Assistente opcional
-------------------

Copie ``.env.example`` para ``.env`` e informe ``OPENAI_API_KEY`` somente se quiser demonstrar a integração externa. A chave permanece no backend e nunca deve ser inserida no dashboard ou versionada.
