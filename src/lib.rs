use v_queue::record::ErrorQueue;
use v_queue::consumer::Consumer;
use v_queue::queue::Queue;
use v_queue::record::MsgType;
use v_queue::record::Mode;
use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use pyo3::types::PyBytes;

// Import from external library
use v_individual_model::onto::individual::{Individual, RawObj};
use v_individual_model::onto::parser::parse_raw;

#[pymodule]
fn vqueue(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<PyQueue>()?;
    m.add_class::<PyConsumer>()?;
    m.add_class::<PyMode>()?;
    m.add_class::<PyMsgType>()?;
    Ok(())
}

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

    fn push(&mut self, data: &PyBytes, msg_type: PyMsgType) -> PyResult<u64> {
        let bytes = data.as_bytes();
        match self.inner.push(bytes, msg_type.into()) {
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

    fn pop_body(&mut self, py: Python) -> PyResult<Option<PyObject>> {
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
    fn convert_individual_to_json(_py: Python, binary_data: &PyBytes) -> PyResult<String> {
        let bytes = binary_data.as_bytes();
        
        // Create Individual from binary data
        let raw = RawObj::new(bytes.to_vec());
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
