import os

from bgl import *

from ..settings import GL_TESS_EVALUATION_SHADER, GL_TESS_CONTROL_SHADER

from .main import BaseShader


class UserShader(BaseShader):
    """Shader compiled from the user's GLSL source files"""
    def __init__(self):
        super().__init__()

        self.prev_mtimes = []
        self.monitored_files = []
        self.stage_filenames = dict()

    def update_settings(self, settings):
        """Update current settings and check if a recompile is necessary
        Raises:
            FileNotFoundError: If the vertex or fragment shader are missing
        Args:
            settings (CSDFRendererSettings): Current settings to read
        """
        if not os.path.isfile(settings.vert_filename):
            raise FileNotFoundError('Missing required vertex shader')

        if not os.path.isfile(settings.frag_filename):
            raise FileNotFoundError('Missing required fragment shader')

        self.stage_filenames = {
            GL_VERTEX_SHADER:           settings.vert_filename,
            GL_TESS_CONTROL_SHADER:     settings.tesc_filename,
            GL_TESS_EVALUATION_SHADER:  settings.tese_filename,
            GL_GEOMETRY_SHADER:         settings.geom_filename,
            GL_FRAGMENT_SHADER:         settings.frag_filename
        }

        self.monitored_files = [f for f in self.stage_filenames.values() if f]

        # Determine if we need to recompile this shader in the render thread.
        # This is based on whether the source files have changed and we're live reloading
        # OR the user has chosen to force reload shaders for whatever reason
        has_source_changes = self.mtimes_changed()
        if settings.force_reload or (settings.live_reload and has_source_changes):
            settings.force_reload = False

            self.load_source_files()
            self.needs_recompile = True

    def load_source_files(self):
        """Read source files into their respective stage buffers for recompilation"""
        self.stage = [f for f in self.stage_filenames]

        for stage in self.STAGES:
            if self.stage_filenames[stage]:
                with open(self.stage_filenames[stage]) as f:
                    self.sources[stage] = f.read()
            else:
                self.sources[stage] = None

        # Update our mtimes to match the last time we read from source files
        self.prev_mtimes = self.mtimes()

    def mtimes(self):
        """Aggregate file modication times from sources"""
        return [os.stat(file).st_mtime for file in self.monitored_files]

    def mtimes_changed(self) -> bool:
        """Check if the file update time has changed in any of the source files"""
        return self.prev_mtimes != self.mtimes()