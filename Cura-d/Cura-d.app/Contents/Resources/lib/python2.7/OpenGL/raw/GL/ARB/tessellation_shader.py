'''Autogenerated by get_gl_extensions script, do not edit!'''
from OpenGL import platform as _p, constants as _cs, arrays
from OpenGL.GL import glget
import ctypes
EXTENSION_NAME = 'GL_ARB_tessellation_shader'
def _f( function ):
    return _p.createFunction( function,_p.GL,'GL_ARB_tessellation_shader',False)
_p.unpack_constants( """GL_PATCHES 0xE
GL_PATCH_VERTICES 0x8E72
GL_PATCH_DEFAULT_INNER_LEVEL 0x8E73
GL_PATCH_DEFAULT_OUTER_LEVEL 0x8E74
GL_TESS_CONTROL_OUTPUT_VERTICES 0x8E75
GL_TESS_GEN_MODE 0x8E76
GL_TESS_GEN_SPACING 0x8E77
GL_TESS_GEN_VERTEX_ORDER 0x8E78
GL_TESS_GEN_POINT_MODE 0x8E79
GL_ISOLINES 0x8E7A
GL_FRACTIONAL_ODD 0x8E7B
GL_FRACTIONAL_EVEN 0x8E7C
GL_MAX_PATCH_VERTICES 0x8E7D
GL_MAX_TESS_GEN_LEVEL 0x8E7E
GL_MAX_TESS_CONTROL_UNIFORM_COMPONENTS 0x8E7F
GL_MAX_TESS_EVALUATION_UNIFORM_COMPONENTS 0x8E80
GL_MAX_TESS_CONTROL_TEXTURE_IMAGE_UNITS 0x8E81
GL_MAX_TESS_EVALUATION_TEXTURE_IMAGE_UNITS 0x8E82
GL_MAX_TESS_CONTROL_OUTPUT_COMPONENTS 0x8E83
GL_MAX_TESS_PATCH_COMPONENTS 0x8E84
GL_MAX_TESS_CONTROL_TOTAL_OUTPUT_COMPONENTS 0x8E85
GL_MAX_TESS_EVALUATION_OUTPUT_COMPONENTS 0x8E86
GL_MAX_TESS_CONTROL_UNIFORM_BLOCKS 0x8E89
GL_MAX_TESS_EVALUATION_UNIFORM_BLOCKS 0x8E8A
GL_MAX_TESS_CONTROL_INPUT_COMPONENTS 0x886C
GL_MAX_TESS_EVALUATION_INPUT_COMPONENTS 0x886D
GL_MAX_COMBINED_TESS_CONTROL_UNIFORM_COMPONENTS 0x8E1E
GL_MAX_COMBINED_TESS_EVALUATION_UNIFORM_COMPONENTS 0x8E1F
GL_UNIFORM_BLOCK_REFERENCED_BY_TESS_CONTROL_SHADER 0x84F0
GL_UNIFORM_BLOCK_REFERENCED_BY_TESS_EVALUATION_SHADER 0x84F1
GL_TESS_EVALUATION_SHADER 0x8E87
GL_TESS_CONTROL_SHADER 0x8E88""", globals())
@_f
@_p.types(None,_cs.GLenum,_cs.GLint)
def glPatchParameteri( pname,value ):pass
@_f
@_p.types(None,_cs.GLenum,arrays.GLfloatArray)
def glPatchParameterfv( pname,values ):pass


def glInitTessellationShaderARB():
    '''Return boolean indicating whether this extension is available'''
    from OpenGL import extensions
    return extensions.hasGLExtension( EXTENSION_NAME )