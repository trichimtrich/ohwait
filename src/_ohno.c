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

    PyObject *g = PyGen_New(f);
    Py_INCREF(g);

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

static PyObject *method_magic(PyObject *self, PyObject *args)
{
    PyBytesObject *new_co_code;
    struct _frame *fr;
    if (!PyArg_ParseTuple(args, "OO", &fr, &new_co_code))
    {
        return NULL;
    }

    PyCodeObject *f_code = fr->f_code;
    PyBytesObject *old_co_code = (PyBytesObject *)f_code->co_code;

    char *old_code_ptr = (char *)PyBytes_AS_STRING(old_co_code);
    int old_code_len = PyBytes_GET_SIZE(old_co_code);
    char *new_code_ptr = (char *)PyBytes_AS_STRING(new_co_code);
    int new_code_len = PyBytes_GET_SIZE(new_co_code);

    printf("old co_code ptr: %p - len: %d\n", old_code_ptr, old_code_len);
    printf("new co_code ptr: %p - len: %d\n", new_code_ptr, new_code_len);

    memcpy(old_code_ptr, new_code_ptr, old_code_len);

    f_code->co_code = new_co_code;
    Py_INCREF(new_co_code);

    // PyObject **specials = hihi->f_valuestack - FRAME_SPECIALS_SIZE;
    // PyCodeObject *my_co = (PyCodeObject *)specials[FRAME_SPECIALS_CODE_OFFSET];
    // printf("%lx - %p\n", my_co, hihi->f_code);
    // hihi->f_code->co_code = co_code;

    return Py_None;
}

static PyMethodDef Methods[] = {
    {"count_sync_funcs", method_count_sync_funcs, METH_VARARGS, ""},
    {"is_injected", method_is_injected, METH_VARARGS, ""},
    {"mark_injected", method_mark_injected, METH_VARARGS, ""},
    {"new_generator", method_new_generator, METH_VARARGS, ""},
    {"replace_co_code", method_replace_co_code, METH_VARARGS, ""},
    {"overwrite_bytes", method_overwrite_bytes, METH_VARARGS, ""},
    {"magic", method_magic, METH_VARARGS, "Python interface for fputs C library function"},
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
