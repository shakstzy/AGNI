# Workflow: Export FHIR Bundle & Health Records

1. Navigate to `https://mychart.austinregionalclinic.com/MyChart/Health/DocumentCenter`.
2. Click "Download My Record" / "Export Health Data".
3. Select FHIR R4 JSON bundle or Continuity of Care Document (C-CDA XML).
4. Save file to `workspaces/health/state/raw/mychart.bundle.json`.
5. Run `./workspaces/health/run ingest --file workspaces/health/state/raw/mychart.bundle.json`.
