#include <Python.h>

// This file serves as a simple C extension module entry point.
// It ensures that the PyInit__obuparse_c function is defined, which is
// required when linking a Python C extension.
// The actual OBU parsing functions from obuparse.c will be part of this
// same compiled library, and _c_wrapper.py will call them using ctypes
// by loading this compiled extension module.

static struct PyModuleDef _obuparse_c_module_def = {
    PyModuleDef_HEAD_INIT,
    "pyobuparse._obuparse_c", // Module name, should match Extension name in setup.py
    NULL,                     // Module documentation (can be NULL)
    -1,                       // Size of per-interpreter state or -1 (usually -1 for simple modules)
    NULL,                     // Method table (can be NULL if no methods are exposed directly from this shim)
    NULL, NULL, NULL, NULL    // Slot definitions for multi-phase initialization (can be NULL)
};

PyMODINIT_FUNC PyInit__obuparse_c(void) {
    // This function is called when Python imports the C extension module.
    // It should return a new module object.
    PyObject *module = PyModule_Create(&_obuparse_c_module_def);
    // if (module == NULL) { // Basic error check
    //     return NULL;
    // }
    // No further initialization of the module object is needed here,
    // as ctypes will access the C functions from obuparse.c directly
    // once this .pyd/.so is loaded.
    return module;
}
