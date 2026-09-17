# Workflow: Fetch Lab Results

1. Navigate to `https://mychart.austinregionalclinic.com/MyChart/Health/TestResults`.
2. Wait for results list container to render.
3. Extract recent metabolic, lipid, HbA1c, and CBC panel values.
4. Pass records into `workspaces/health/import_mychart.py`.
