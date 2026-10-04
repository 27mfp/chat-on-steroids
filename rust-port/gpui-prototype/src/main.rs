use std::sync::Arc;

use gpui::{
    App, Bounds, Context, ListAlignment, ListState, Render, Window, WindowBounds, WindowOptions,
    div, list, prelude::*, px, rgb, size,
};
use gpui_platform::application;

mod fixtures;

use fixtures::{TranscriptKind, TranscriptRow, synthetic_transcript_from};

const TRANSCRIPT_ROWS: usize = 10_000;
const FIRST_ROW_ID: usize = 10_001;
const PREPEND_ROWS: usize = 25;

const PAGE: u32 = 0x111318;
const SIDEBAR: u32 = 0x171A20;
const CARD: u32 = 0x1D2128;
const HOVER: u32 = 0x232832;
const LINE: u32 = 0x292E37;
const EDGE: u32 = 0x353B46;
const INK: u32 = 0xF1F3F5;
const SOFT: u32 = 0xB2B8C2;
const FAINT: u32 = 0x7F8794;
const GREEN: u32 = 0x66C78F;

struct PrototypeApp {
    rows: Arc<Vec<TranscriptRow>>,
    list_state: ListState,
}

impl PrototypeApp {
    fn new() -> Self {
        let rows = Arc::new(synthetic_transcript_from(FIRST_ROW_ID, TRANSCRIPT_ROWS));
        let list_state = ListState::new(rows.len(), ListAlignment::Top, px(900.));

        Self { rows, list_state }
    }

    fn prepend_older(&mut self) -> bool {
        let first_id = self.rows[0].id;
        if first_id <= PREPEND_ROWS {
            return false;
        }
        let older = synthetic_transcript_from(first_id - PREPEND_ROWS, PREPEND_ROWS);
        Arc::make_mut(&mut self.rows).splice(0..0, older);
        self.list_state.splice(0..0, PREPEND_ROWS);
        true
    }
}

impl Render for PrototypeApp {
    fn render(&mut self, _window: &mut Window, cx: &mut Context<Self>) -> impl IntoElement {
        let rows = self.rows.clone();

        div()
            .size_full()
            .flex()
            .flex_col()
            .bg(rgb(PAGE))
            .text_color(rgb(INK))
            .child(
                div()
                    .h(px(30.))
                    .flex_shrink_0()
                    .flex()
                    .items_center()
                    .gap_2()
                    .px_3()
                    .bg(rgb(SIDEBAR))
                    .border_b_1()
                    .border_color(rgb(LINE))
                    .text_xs()
                    .child(div().px_1().text_color(rgb(SOFT)).child("☰"))
                    .child(div().px_2().child("View"))
                    .child(
                        div()
                            .ml_auto()
                            .text_color(rgb(FAINT))
                            .child("Native GPUI feasibility build"),
                    ),
            )
            .child(
                div()
                    .flex_1()
                    .min_h(px(0.))
                    .flex()
                    .child(
                        div()
                            .w(px(272.))
                            .h_full()
                            .flex_shrink_0()
                            .flex()
                            .flex_col()
                            .bg(rgb(SIDEBAR))
                            .border_r_1()
                            .border_color(rgb(LINE))
                            .p_3()
                            .child(
                                div()
                                    .px_2()
                                    .pt_2()
                                    .pb_4()
                                    .text_base()
                                    .font_weight(gpui::FontWeight::SEMIBOLD)
                                    .child("Chat On Steroids"),
                            )
                            .child(
                                div()
                                    .h(px(38.))
                                    .flex()
                                    .items_center()
                                    .gap_2()
                                    .px_3()
                                    .rounded_lg()
                                    .child(div().text_lg().child("+") )
                                    .child("New chat"),
                            )
                            .child(
                                div()
                                    .h(px(38.))
                                    .flex()
                                    .items_center()
                                    .gap_2()
                                    .px_3()
                                    .rounded_lg()
                                    .text_color(rgb(SOFT))
                                    .child(div().w(px(18.)).child("◇"))
                                    .child("Plugins"),
                            )
                            .child(
                                div()
                                    .h(px(38.))
                                    .flex()
                                    .items_center()
                                    .gap_2()
                                    .px_3()
                                    .rounded_lg()
                                    .text_color(rgb(SOFT))
                                    .child(div().w(px(18.)).child("◫"))
                                    .child("Skills"),
                            )
                            .child(
                                div()
                                    .h(px(38.))
                                    .flex()
                                    .items_center()
                                    .gap_2()
                                    .px_3()
                                    .rounded_lg()
                                    .text_color(rgb(SOFT))
                                    .child(div().w(px(18.)).child("✦"))
                                    .child("Pets"),
                            )
                            .child(
                                div()
                                    .mt_4()
                                    .px_2()
                                    .py_2()
                                    .flex()
                                    .items_center()
                                    .text_xs()
                                    .font_weight(gpui::FontWeight::SEMIBOLD)
                                    .text_color(rgb(FAINT))
                                    .child("▾  Projects")
                                    .child(div().ml_auto().text_base().child("+")),
                            )
                            .child(
                                div()
                                    .h(px(38.))
                                    .flex()
                                    .items_center()
                                    .px_3()
                                    .rounded_lg()
                                    .bg(rgb(HOVER))
                                    .child(
                                        div()
                                            .flex_1()
                                            .min_w(px(0.))
                                            .child("GPUI frontend port"),
                                    ),
                            )
                            .child(
                                div()
                                    .h(px(34.))
                                    .flex()
                                    .items_center()
                                    .px_3()
                                    .text_sm()
                                    .text_color(rgb(SOFT))
                                    .child("Chat On Steroids"),
                            )
                            .child(
                                div()
                                    .mt_3()
                                    .px_2()
                                    .py_2()
                                    .flex()
                                    .items_center()
                                    .text_xs()
                                    .font_weight(gpui::FontWeight::SEMIBOLD)
                                    .text_color(rgb(FAINT))
                                    .child("▾  Chats"),
                            )
                            .child(
                                div()
                                    .h(px(34.))
                                    .flex()
                                    .items_center()
                                    .px_3()
                                    .text_sm()
                                    .text_color(rgb(SOFT))
                                    .child("GPUI research notes"),
                            )
                            .child(
                                div()
                                    .h(px(34.))
                                    .flex()
                                    .items_center()
                                    .px_3()
                                    .text_sm()
                                    .text_color(rgb(SOFT))
                                    .child("Renderer parity audit"),
                            )
                            .child(div().flex_1())
                            .child(
                                div()
                                    .pt_3()
                                    .border_t_1()
                                    .border_color(rgb(LINE))
                                    .flex()
                                    .items_center()
                                    .gap_2()
                                    .child(
                                        div()
                                            .h(px(36.))
                                            .flex_1()
                                            .flex()
                                            .items_center()
                                            .gap_2()
                                            .px_3()
                                            .rounded_lg()
                                            .text_color(rgb(SOFT))
                                            .child("⚙")
                                            .child("Settings"),
                                    )
                                    .child(
                                        div()
                                            .size(px(36.))
                                            .flex()
                                            .items_center()
                                            .justify_center()
                                            .border_1()
                                            .border_color(rgb(LINE))
                                            .rounded_lg()
                                            .child(div().size(px(8.)).rounded_full().bg(rgb(GREEN))),
                                    ),
                            ),
                    )
                    .child(
                        div()
                            .flex_1()
                            .min_w(px(0.))
                            .h_full()
                            .flex()
                            .flex_col()
                            .child(
                                div()
                                    .h(px(48.))
                                    .flex_shrink_0()
                                    .flex()
                                    .items_center()
                                    .gap_3()
                                    .px_5()
                                    .border_b_1()
                                    .border_color(rgb(LINE))
                                    .child(
                                        div()
                                            .text_sm()
                                            .font_weight(gpui::FontWeight::SEMIBOLD)
                                            .child("GPUI frontend port"),
                                    )
                                    .child(div().text_color(rgb(FAINT)).child("/"))
                                    .child(div().text_xs().text_color(rgb(FAINT)).child("chat-on-steroids"))
                                    .child(
                                        div()
                                            .id("prepend-older")
                                            .cursor_pointer()
                                            .px_2()
                                            .py_1()
                                            .rounded_lg()
                                            .bg(rgb(HOVER))
                                            .text_xs()
                                            .child("Prepend 25 older rows")
                                            .on_click(cx.listener(|this, _, _, cx| {
                                                if this.prepend_older() {
                                                    cx.notify();
                                                }
                                            })),
                                    )
                                    .child(
                                        div()
                                            .ml_auto()
                                            .flex()
                                            .items_center()
                                            .gap_2()
                                            .text_xs()
                                            .text_color(rgb(SOFT))
                                            .child(div().size(px(7.)).rounded_full().bg(rgb(GREEN)))
                                            .child("Prototype"),
                                    ),
                            )
                            .child(
                                div()
                                    .flex_1()
                                    .min_h(px(0.))
                                    .flex()
                                    .flex_col()
                                    .child(
                                        list(self.list_state.clone(), move |index, _window, _cx| {
                                            let row = &rows[index];
                                            let content = div()
                                                .w_full()
                                                .max_w(px(860.))
                                                .mx_auto();

                                            match row.kind {
                                                TranscriptKind::User => content
                                                    .flex()
                                                    .justify_end()
                                                    .child(
                                                        div()
                                                            .max_w(px(700.))
                                                            .px_4()
                                                            .py_3()
                                                            .rounded_xl()
                                                            .bg(rgb(HOVER))
                                                            .text_sm()
                                                            .line_height(px(22.))
                                                            .child(row.body.clone()),
                                                    )
                                                    .into_any(),
                                                TranscriptKind::Assistant => content
                                                    .child(
                                                        div()
                                                            .mb_2()
                                                            .text_xs()
                                                            .font_weight(gpui::FontWeight::SEMIBOLD)
                                                            .text_color(rgb(SOFT))
                                                            .child("ChatGPT"),
                                                    )
                                                    .child(
                                                        div()
                                                            .text_sm()
                                                            .line_height(px(23.))
                                                            .child(row.body.clone()),
                                                    )
                                                    .into_any(),
                                                TranscriptKind::Tool => content
                                                    .child(
                                                        div()
                                                            .border_1()
                                                            .border_color(rgb(LINE))
                                                            .rounded_lg()
                                                            .bg(rgb(SIDEBAR))
                                                            .px_3()
                                                            .py_2()
                                                            .text_xs()
                                                            .text_color(rgb(SOFT))
                                                            .child(
                                                                div()
                                                                    .flex()
                                                                    .items_center()
                                                                    .gap_2()
                                                                    .mb_1()
                                                                    .font_weight(gpui::FontWeight::SEMIBOLD)
                                                                    .child("Tool result")
                                                                    .child(
                                                                        div()
                                                                            .text_color(rgb(FAINT))
                                                                            .child(format!("#{}", row.id)),
                                                                    ),
                                                            )
                                                            .child(row.body.clone()),
                                                    )
                                                    .into_any(),
                                            }
                                        })
                                        .flex_1()
                                        .px_5()
                                        .py_4(),
                                    )
                                    .child(
                                        div()
                                            .w_full()
                                            .px_5()
                                            .pb_5()
                                            .pt_2()
                                            .child(
                                                div()
                                                    .w_full()
                                                    .max_w(px(860.))
                                                    .mx_auto()
                                                    .border_1()
                                                    .border_color(rgb(EDGE))
                                                    .rounded_xl()
                                                    .bg(rgb(CARD))
                                                    .p_3()
                                                    .child(
                                                        div()
                                                            .min_h(px(46.))
                                                            .px_1()
                                                            .text_base()
                                                            .text_color(rgb(FAINT))
                                                            .child("Ask anything…"),
                                                    )
                                                    .child(
                                                        div()
                                                            .h(px(36.))
                                                            .flex()
                                                            .items_center()
                                                            .gap_1()
                                                            .child(
                                                                div()
                                                                    .size(px(34.))
                                                                    .flex()
                                                                    .items_center()
                                                                    .justify_center()
                                                                    .rounded_lg()
                                                                    .text_lg()
                                                                    .text_color(rgb(SOFT))
                                                                    .child("+"),
                                                            )
                                                            .child(
                                                                div()
                                                                    .h(px(34.))
                                                                    .flex()
                                                                    .items_center()
                                                                    .px_2()
                                                                    .rounded_lg()
                                                                    .text_xs()
                                                                    .text_color(rgb(SOFT))
                                                                    .child("Normal  ▾"),
                                                            )
                                                            .child(
                                                                div()
                                                                    .h(px(34.))
                                                                    .flex()
                                                                    .items_center()
                                                                    .px_2()
                                                                    .rounded_lg()
                                                                    .text_xs()
                                                                    .text_color(rgb(SOFT))
                                                                    .child("Plan"),
                                                            )
                                                            .child(
                                                                div()
                                                                    .ml_auto()
                                                                    .size(px(28.))
                                                                    .rounded_full()
                                                                    .border_1()
                                                                    .border_color(rgb(LINE))
                                                                    .flex()
                                                                    .items_center()
                                                                    .justify_center()
                                                                    .text_xs()
                                                                    .text_color(rgb(FAINT))
                                                                    .child("0"),
                                                            )
                                                            .child(
                                                                div()
                                                                    .h(px(34.))
                                                                    .flex()
                                                                    .items_center()
                                                                    .px_2()
                                                                    .rounded_lg()
                                                                    .text_xs()
                                                                    .text_color(rgb(SOFT))
                                                                    .child("GPT-5.6 Sol  ▾"),
                                                            )
                                                            .child(
                                                                div()
                                                                    .size(px(34.))
                                                                    .rounded_full()
                                                                    .bg(rgb(INK))
                                                                    .text_color(rgb(PAGE))
                                                                    .flex()
                                                                    .items_center()
                                                                    .justify_center()
                                                                    .text_base()
                                                                    .font_weight(gpui::FontWeight::SEMIBOLD)
                                                                    .child("↑"),
                                                            ),
                                                    ),
                                            ),
                                    ),
                            ),
                    ),
            )
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use gpui::{ListOffset, TestAppContext};

    #[gpui::test]
    fn prepend_keeps_row_identity_and_intra_row_offset(_cx: &mut TestAppContext) {
        let mut app = PrototypeApp::new();
        app.list_state.scroll_to(ListOffset {
            item_ix: 120,
            offset_in_item: px(7.),
        });
        let before = app.list_state.logical_scroll_top();
        let anchor_id = app.rows[before.item_ix].id;

        assert!(app.prepend_older());
        let after = app.list_state.logical_scroll_top();
        assert_eq!(after.item_ix, before.item_ix + PREPEND_ROWS);
        assert_eq!(after.offset_in_item, before.offset_in_item);
        assert_eq!(app.rows[after.item_ix].id, anchor_id);
        assert_eq!(app.rows[0].id, FIRST_ROW_ID - PREPEND_ROWS);
        assert_eq!(app.rows.len(), TRANSCRIPT_ROWS + PREPEND_ROWS);

        // Replacing the list is not an anchored prepend: the index now names a different row.
        let reset = ListState::new(app.rows.len(), ListAlignment::Top, px(900.));
        reset.scroll_to(before);
        assert_ne!(app.rows[reset.logical_scroll_top().item_ix].id, anchor_id);
    }

    #[gpui::test]
    fn prepend_stops_at_oldest_fixture_id(_cx: &mut TestAppContext) {
        let mut app = PrototypeApp::new();
        for _ in 0..(FIRST_ROW_ID - 1) / PREPEND_ROWS {
            assert!(app.prepend_older());
        }
        assert_eq!(app.rows[0].id, 1);
        assert!(!app.prepend_older());
        assert_eq!(app.rows[0].id, 1);
    }
}

fn main() {
    application().run(|cx: &mut App| {
        let bounds = Bounds::centered(None, size(px(1280.), px(820.)), cx);

        cx.open_window(
            WindowOptions {
                focus: true,
                window_bounds: Some(WindowBounds::Windowed(bounds)),
                ..Default::default()
            },
            |_, cx| cx.new(|_| PrototypeApp::new()),
        )
        .expect("open GPUI prototype window");

        cx.activate(true);
    });
}
