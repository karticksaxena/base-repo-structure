"""Code shared by 2+ features (NestJS `common/`): domain errors, guards, utils, constants.

Any module may import from here; this package may use `core.config` / `core.logger` but never
a feature. Move code here only when a second feature needs it.
"""
