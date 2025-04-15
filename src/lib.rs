use v_queue::record::ErrorQueue;
use v_queue::consumer::Consumer;
use v_queue::queue::Queue;
use v_queue::record::MsgType;
use v_queue::record::Mode;
use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use pyo3::types::PyBytes;
use pyo3::PyObject;

// Import from external library
use v_individual_model::onto::individual::{Individual, RawObj};
use v_individual_model::onto::parser::parse_raw;

#[pyclass(name = "Mode")]
#[derive(Clone, Copy)]
pub enum PyMode {
    #[pyo3(name = "READ")]
    Read = 0,
    #[pyo3(name = "READ_WRITE")]
    ReadWrite = 1,
    #[pyo3(name = "DEFAULT")]
    Default = 2,
}

#[pymethods]
impl PyMode {
    fn __str__(&self) -> &'static str {
        match self {
            PyMode::Read => "READ",
            PyMode::ReadWrite => "READ_WRITE",
            PyMode::Default => "DEFAULT",
        }
    }
}

impl From<PyMode> for Mode {
    fn from(mode: PyMode) -> Self {
        match mode {
            PyMode::Read => Mode::Read,
            PyMode::ReadWrite => Mode::ReadWrite,
            PyMode::Default => Mode::Default,
        }
    }
}

#[pyclass(name = "MsgType")]
#[derive(Clone, Copy)]
pub enum PyMsgType {
    #[pyo3(name = "STRING")]
    String = b'S' as isize,
    #[pyo3(name = "OBJECT")]
    Object = b'O' as isize,
}

#[pymethods]
impl PyMsgType {
    fn __str__(&self) -> &'static str {
        match self {
            PyMsgType::String => "STRING",
            PyMsgType::Object => "OBJECT",
        }
    }
}

impl From<PyMsgType> for MsgType {
    fn from(msg_type: PyMsgType) -> Self {
        match msg_type {
            PyMsgType::String => MsgType::String,
            PyMsgType::Object => MsgType::Object,
        }
    }
}

#[pyclass(name = "Queue")]
pub struct PyQueue {
    inner: Queue,
}

#[pymethods]
impl PyQueue {
    #[new]
    fn new(base_path: String, queue_name: String, mode: PyMode) -> PyResult<Self> {
        match Queue::new(&base_path, &queue_name, mode.into()) {
            Ok(queue) => Ok(PyQueue { inner: queue }),
            Err(e) => Err(PyValueError::new_err(e.as_str().to_string())),
        }
    }

    fn push(&mut self, py: Python<'_>, data: PyObject, msg_type: PyMsgType) -> PyResult<u64> {
        // Convert PyObject to bytes
        let bytes = py_to_bytes(py, data)?;

        match self.inner.push(&bytes, msg_type.into()) {
            Ok(pos) => Ok(pos),
            Err(e) => Err(PyValueError::new_err(e.as_str().to_string())),
        }
    }

    #[getter]
    fn count_pushed(&self) -> u32 {
        self.inner.count_pushed
    }

    #[getter]
    fn name(&self) -> String {
        self.inner.name.clone()
    }

    #[getter]
    fn is_ready(&self) -> bool {
        self.inner.is_ready
    }
}

#[pyclass(name = "Consumer")]
pub struct PyConsumer {
    inner: Consumer,
}

#[pymethods]
impl PyConsumer {
    #[new]
    fn new(base_path: String, consumer_name: String, queue_name: String) -> PyResult<Self> {
        match Consumer::new(&base_path, &consumer_name, &queue_name) {
            Ok(consumer) => Ok(PyConsumer { inner: consumer }),
            Err(e) => Err(PyValueError::new_err(e.as_str().to_string())),
        }
    }

    #[staticmethod]
    fn new_with_mode(base_path: String, consumer_name: String, queue_name: String, mode: PyMode) -> PyResult<Self> {
        match Consumer::new_with_mode(&base_path, &consumer_name, &queue_name, mode.into()) {
            Ok(consumer) => Ok(PyConsumer { inner: consumer }),
            Err(e) => Err(PyValueError::new_err(e.as_str().to_string())),
        }
    }

    fn pop_header(&mut self) -> bool {
        self.inner.pop_header()
    }

    fn pop_body(&mut self, py: Python<'_>) -> PyResult<Option<PyObject>> {
        let msg_size = self.inner.header.msg_length as usize;
        let mut buffer = vec![0u8; msg_size];

        match self.inner.pop_body(&mut buffer) {
            Ok(_) => {
                let bytes = PyBytes::new(py, &buffer);
                Ok(Some(bytes.into()))
            },
            Err(e) => {
                if e == ErrorQueue::FailReadTailMessage {
                    Ok(None)
                } else {
                    Err(PyValueError::new_err(e.as_str().to_string()))
                }
            }
        }
    }

    /// Converts binary data in Individual format to JSON string
    /// This is a static method that can be used independently of queue operations
    #[staticmethod]
    fn convert_individual_to_json(py: Python<'_>, binary_data: PyObject) -> PyResult<String> {
        // Convert PyObject to bytes
        let bytes = py_to_bytes(py, binary_data)?;

        // Create Individual from binary data
        let raw = RawObj::new(bytes);
        let mut individual = Individual::new_raw(raw);

        // Parse the raw data (initial parsing)
        if let Err(_) = parse_raw(&mut individual) {
            return Err(PyValueError::new_err("Failed to parse binary data to Individual"));
        }

        // Fully parse all predicates and resources (Individual uses lazy parsing)
        individual.parse_all();

        // Convert Individual to JSON
        let json_str = individual.get_obj().as_json_str();

        if json_str.is_empty() {
            return Err(PyValueError::new_err("Failed to convert Individual to JSON"));
        }

        Ok(json_str)
    }

    fn commit(&mut self) -> bool {
        self.inner.commit()
    }

    fn get_batch_size(&mut self) -> u32 {
        self.inner.get_batch_size()
    }

    #[getter]
    fn count_popped(&self) -> u32 {
        self.inner.count_popped
    }

    #[getter]
    fn name(&self) -> String {
        self.inner.name.clone()
    }
}

/// Helper function to convert PyObject to Vec<u8>
fn py_to_bytes(py: Python<'_>, obj: PyObject) -> PyResult<Vec<u8>> {
    // Try to downcast to PyBytes
    if let Ok(bytes) = obj.downcast_bound::<PyBytes>(py) {
        let len = unsafe { pyo3::ffi::PyBytes_Size(bytes.as_ptr()) as usize };
        let data = unsafe { pyo3::ffi::PyBytes_AsString(bytes.as_ptr()) as *const u8 };
        let bytes_slice = unsafe { std::slice::from_raw_parts(data, len) };
        Ok(bytes_slice.to_vec())
    } else {
        Err(PyValueError::new_err("Expected bytes object"))
    }
}

/// Python module initialization
#[pymodule]
fn vqueue(py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Add classes to the module
    m.add("Queue", py.get_type::<PyQueue>())?;
    m.add("Consumer", py.get_type::<PyConsumer>())?;
    m.add("Mode", py.get_type::<PyMode>())?;
    m.add("MsgType", py.get_type::<PyMsgType>())?;
    Ok(())
}