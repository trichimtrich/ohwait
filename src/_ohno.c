#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <frameobject.h>

// TODO: fix ref count

#define CO_INJECTED 0x80000000

// count upward for sync funcs called
static PyObject *method_count_sync_funcs(PyObject *self, PyObject *args)
{
    struct _frame *f = PyEval_GetFrame();
    int c = 0;
    // ignore current frame
    for (f = f->f_back; f && !(f->f_code->co_flags & CO_COROUTINE); f = f->f_back, c++)
    {
    }

    if (f == NULL)
    {
        return PyLong_FromLong(-1);
    }

    return PyLong_FromLong(c);
}

// check if injected
static PyObject *method_is_injected(PyObject *self, PyObject *args)
{
    PyCodeObject *co;
    if (!PyArg_ParseTuple(args, "O", &co))
    {
        return NULL;
    }

    return PyBool_FromLong(co->co_flags & CO_INJECTED);
}

// mark injected
static PyObject *method_mark_injected(PyObject *self, PyObject *args)
{
    PyCodeObject *co;
    if (!PyArg_ParseTuple(args, "O", &co))
    {
        return NULL;
    }

    co->co_flags |= CO_INJECTED;

    return Py_True;
}

// create generator object from frame
static PyObject *method_new_generator(PyObject *self, PyObject *args)
{
    struct _frame *f;
    if (!PyArg_ParseTuple(args, "O", &f))
    {
        return NULL;
    }

    Py_INCREF(f);
    PyObject *g = PyGen_New(f);

    return g;
}

// replace co_code bytes of code object
static PyObject *method_replace_co_code(PyObject *self, PyObject *args)
{
    PyBytesObject *co_code;
    PyCodeObject *co;
    if (!PyArg_ParseTuple(args, "OO", &co, &co_code))
    {
        return NULL;
    }

    co->co_code = co_code;
    Py_INCREF(co_code);

    return Py_True;
}

// overwrite data in bytes object
static PyObject *method_overwrite_bytes(PyObject *self, PyObject *args)
{
    PyBytesObject *b_obj;
    int offset;
    PyBytesObject *payload;
    if (!PyArg_ParseTuple(args, "OiO", &b_obj, &offset, &payload))
    {
        return NULL;
    }

    char *b_ptr = (char *)PyBytes_AS_STRING(b_obj);

    char *p_ptr = (char *)PyBytes_AS_STRING(payload);
    int p_len = PyBytes_GET_SIZE(payload);

    memcpy(b_ptr + offset, p_ptr, p_len);

    return Py_True;
}

static PyMethodDef Methods[] = {
    {"count_sync_funcs", method_count_sync_funcs, METH_VARARGS, ""},
    {"is_injected", method_is_injected, METH_VARARGS, ""},
    {"mark_injected", method_mark_injected, METH_VARARGS, ""},
    {"new_generator", method_new_generator, METH_VARARGS, ""},
    {"replace_co_code", method_replace_co_code, METH_VARARGS, ""},
    {"overwrite_bytes", method_overwrite_bytes, METH_VARARGS, ""},
    {NULL, NULL, 0, NULL}};

static struct PyModuleDef module = {
    PyModuleDef_HEAD_INIT,
    "ohwait._ohno",
    "",
    -1,
    Methods};

PyMODINIT_FUNC PyInit__ohno(void)
{
    return PyModule_Create(&module);
}
