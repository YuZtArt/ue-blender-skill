# Host-Specific Work

## Unreal Engine

MCP actions commonly execute on the editor/game thread. Before a substantial mutation, confirm responsiveness and check for compilation, a modal dialog, PIE transition, import, or save. Record the target asset path and relevant pre-change state. Change and verify one asset at a time unless the task requires a bulk operation.

Query the installed server's schemas. UEMCP and Monolith versions can advertise different tools; the CLI's `ue` shorthand assumes Monolith `<namespace>_query` actions. Use generic `call` for other advertised tools. If `monolith_status` is absent, use `tools unreal` to select a small read-only check rather than assuming the host is down.

## Blender

BlenderMCP executes code on the main thread. Inspect the actual scene, Blender version, and required API or node sockets before editing. Do not assume object names, modes, or defaults.

Imports, dependency-graph updates, renders, and large mesh loops can block MCP. Separate setup, analysis, mutation, and verification. For an inherently long single operation, announce it, select an appropriate timeout, and poll the existing outer session without concurrent Blender heartbeats.

Preserve unrelated objects and unsaved work. Save to the user-requested file or a clearly identified output path when saving is part of the task.

## Blender To Unreal

Inspect source geometry, transforms, units, materials, and the destination before choosing export settings. Establish an explicit export path and Unreal destination package. Export and verify the file, then import and inspect the resulting asset in a separate call. Check scale, orientation, materials, and the requested appearance or behavior. Save only the requested outputs.

This skill supplies orchestration, not a universal FBX or glTF preset. Use the installed exporter/importer schemas and the task's requirements.
