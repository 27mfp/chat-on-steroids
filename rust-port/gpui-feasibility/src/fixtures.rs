use gpui::SharedString;

pub const LOGICAL_ROW_COUNT: usize = 10_000;
pub const LOADED_ROW_COUNT: usize = 320;
pub const WINDOW_STEP: usize = 240;

#[derive(Clone)]
pub struct MessageFixture {
    pub logical_index: usize,
    pub kind: &'static str,
    pub body: SharedString,
    pub height: f32,
}

impl MessageFixture {
    pub fn new(logical_index: usize) -> Self {
        let (kind, body, height) = match logical_index % 7 {
            0 => (
                "user",
                format!(
                    "User request #{logical_index}: inspect the current owner before changing state."
                ),
                58.0,
            ),
            1 => (
                "assistant",
                "A longer assistant response with wrapped text. This fixture exists to make row heights differ and to exercise scrolling through mixed transcript content without mounting all logical rows at once.".to_owned(),
                92.0,
            ),
            2 => (
                "tool",
                "Tool result: build completed with structured evidence and a bounded output preview.".to_owned(),
                70.0,
            ),
            3 => (
                "assistant/code",
                "fn reconcile(owner: SessionId, epoch: Epoch) {\n    assert_current(owner, epoch);\n    publish_projection();\n}".to_owned(),
                118.0,
            ),
            4 => (
                "status",
                "Queued input is admitted locally; browser delivery is still unconfirmed.".to_owned(),
                62.0,
            ),
            5 => (
                "assistant",
                "Image placeholder completed after the row was initially visible. The prototype keeps this synthetic so no filesystem or backend owner is involved.".to_owned(),
                86.0,
            ),
            _ => (
                "user",
                "Follow-up correction preserving the original objective and extending the current task.".to_owned(),
                64.0,
            ),
        };

        Self {
            logical_index,
            kind,
            body: body.into(),
            height,
        }
    }
}
