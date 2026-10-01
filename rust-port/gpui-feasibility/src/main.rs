mod fixtures;

use std::path::PathBuf;

use fixtures::{LOADED_ROW_COUNT, LOGICAL_ROW_COUNT, MessageFixture, WINDOW_STEP};
use gpui::{
    App, Bounds, Context, ExternalPaths, FocusHandle, ListAlignment, ListState, Render, Role,
    SharedString, Toggled, Window, WindowBounds, WindowOptions, div, list, prelude::*, px, rgb,
    size, text,
};
use gpui_platform::application;

struct Prototype {
    rows: Vec<MessageFixture>,
    window_start: usize,
    list_state: ListState,
    composer_focus: FocusHandle,
    composer: String,
    dark: bool,
    text_scale: f32,
    dock_width: f32,
    dropped_paths: Vec<PathBuf>,
}

impl Prototype {
    fn new(window: &mut Window, cx: &mut Context<Self>) -> Self {
        let composer_focus = cx.focus_handle();
        window.focus(&composer_focus, cx);

        Self {
            rows: (0..LOGICAL_ROW_COUNT).map(MessageFixture::new).collect(),
            window_start: LOGICAL_ROW_COUNT - LOADED_ROW_COUNT,
            list_state: ListState::new(LOADED_ROW_COUNT, ListAlignment::Bottom, px(760.0))
                .measure_all(),
            composer_focus,
            composer: "Try multiline editing here.\nShift+Enter is represented as another newline in this feasibility slice.".to_owned(),
            dark: true,
            text_scale: 1.0,
            dock_width: 260.0,
            dropped_paths: Vec::new(),
        }
    }

    fn shift_window(&mut self, direction: isize, cx: &mut Context<Self>) {
        let max_start = LOGICAL_ROW_COUNT.saturating_sub(LOADED_ROW_COUNT);
        self.window_start = if direction < 0 {
            self.window_start.saturating_sub(WINDOW_STEP)
        } else {
            self.window_start.saturating_add(WINDOW_STEP).min(max_start)
        };
        self.list_state =
            ListState::new(LOADED_ROW_COUNT, ListAlignment::Bottom, px(760.0)).measure_all();
        cx.notify();
    }

    fn handle_composer_key(&mut self, event: &gpui::KeyDownEvent, cx: &mut Context<Self>) {
        if event.keystroke.key == "backspace" {
            self.composer.pop();
            cx.notify();
            return;
        }

        if event.keystroke.key == "enter" {
            self.composer.push('\n');
            cx.notify();
            return;
        }

        if event.keystroke.modifiers.control || event.keystroke.modifiers.platform {
            return;
        }

        if let Some(value) = event.keystroke.key_char.as_deref() {
            if !value.chars().any(char::is_control) {
                self.composer.push_str(value);
                cx.notify();
            }
        }
    }

    fn palette(&self) -> (gpui::Rgba, gpui::Rgba, gpui::Rgba, gpui::Rgba) {
        if self.dark {
            (rgb(0x14161c), rgb(0x1d2028), rgb(0xe7e9ef), rgb(0x80889a))
        } else {
            (rgb(0xf4f5f8), rgb(0xffffff), rgb(0x20232b), rgb(0x6c7280))
        }
    }
}

impl Render for Prototype {
    fn render(&mut self, _window: &mut Window, cx: &mut Context<Self>) -> impl IntoElement {
        let (page, panel, ink, muted) = self.palette();
        let window_start = self.window_start;
        let rows = self.rows.clone();
        let composer_lines = self
            .composer
            .lines()
            .map(|line| SharedString::from(if line.is_empty() { " " } else { line }))
            .collect::<Vec<_>>();
        let drop_label = if self.dropped_paths.is_empty() {
            "Drop files here to exercise native external-path delivery".to_owned()
        } else {
            format!("{} dropped path(s)", self.dropped_paths.len())
        };

        div()
            .id("prototype-root")
            .role(Role::Application)
            .aria_label("Chat On Steroids GPUI feasibility prototype")
            .size_full()
            .flex()
            .flex_col()
            .bg(page)
            .text_color(ink)
            .text_size(px(14.0 * self.text_scale))
            .child(
                div()
                    .h(px(46.0))
                    .flex_none()
                    .flex()
                    .items_center()
                    .justify_between()
                    .px_4()
                    .border_b_1()
                    .border_color(muted.opacity(0.25))
                    .child(
                        div()
                            .id("prototype-heading")
                            .role(Role::Heading)
                            .aria_level(1)
                            .aria_label("GPUI feasibility prototype")
                            .font_weight(gpui::FontWeight::SEMIBOLD)
                            .child(text!("GPUI feasibility prototype")),
                    )
                    .child(
                        div()
                            .flex()
                            .gap_2()
                            .child(
                                div()
                                    .id("theme-toggle")
                                    .focusable()
                                    .tab_stop(true)
                                    .role(Role::Switch)
                                    .aria_label("Dark theme")
                                    .aria_toggled(if self.dark {
                                        Toggled::True
                                    } else {
                                        Toggled::False
                                    })
                                    .px_3()
                                    .py_1()
                                    .rounded_md()
                                    .bg(panel)
                                    .cursor_pointer()
                                    .on_click(cx.listener(|this, _, _, cx| {
                                        this.dark = !this.dark;
                                        cx.notify();
                                    }))
                                    .child(if self.dark { "Dark" } else { "Light" }),
                            )
                            .child(
                                div()
                                    .id("text-smaller")
                                    .focusable()
                                    .tab_stop(true)
                                    .role(Role::Button)
                                    .aria_label("Decrease text size")
                                    .px_3()
                                    .py_1()
                                    .rounded_md()
                                    .bg(panel)
                                    .cursor_pointer()
                                    .on_click(cx.listener(|this, _, _, cx| {
                                        this.text_scale = (this.text_scale - 0.1).max(0.8);
                                        cx.notify();
                                    }))
                                    .child("A-"),
                            )
                            .child(
                                div()
                                    .id("text-larger")
                                    .focusable()
                                    .tab_stop(true)
                                    .role(Role::Button)
                                    .aria_label("Increase text size")
                                    .px_3()
                                    .py_1()
                                    .rounded_md()
                                    .bg(panel)
                                    .cursor_pointer()
                                    .on_click(cx.listener(|this, _, _, cx| {
                                        this.text_scale = (this.text_scale + 0.1).min(1.5);
                                        cx.notify();
                                    }))
                                    .child("A+"),
                            ),
                    ),
            )
            .child(
                div()
                    .flex_1()
                    .min_h_0()
                    .flex()
                    .child(
                        div()
                            .id("session-navigation")
                            .w(px(210.0))
                            .flex_none()
                            .p_3()
                            .border_r_1()
                            .border_color(muted.opacity(0.25))
                            .bg(panel)
                            .role(Role::Navigation)
                            .aria_label("Synthetic sessions")
                            .child(
                                div()
                                    .font_weight(gpui::FontWeight::SEMIBOLD)
                                    .mb_2()
                                    .child("Sessions"),
                            )
                            .children((0usize..8).map(|index| {
                                div()
                                    .id(("session", index))
                                    .focusable()
                                    .tab_stop(true)
                                    .role(Role::Button)
                                    .aria_label(SharedString::from(format!(
                                        "Synthetic session {}",
                                        index + 1
                                    )))
                                    .w_full()
                                    .px_2()
                                    .py_2()
                                    .mb_1()
                                    .rounded_md()
                                    .hover(|el| el.bg(muted.opacity(0.12)))
                                    .child(format!("Synthetic session {}", index + 1))
                            })),
                    )
                    .child(
                        div()
                            .flex_1()
                            .min_w_0()
                            .flex()
                            .flex_col()
                            .child(
                                div()
                                    .h(px(40.0))
                                    .flex_none()
                                    .flex()
                                    .items_center()
                                    .justify_between()
                                    .px_3()
                                    .border_b_1()
                                    .border_color(muted.opacity(0.25))
                                    .child(format!(
                                        "logical rows: {LOGICAL_ROW_COUNT} · loaded: {}..{}",
                                        window_start,
                                        window_start + LOADED_ROW_COUNT - 1
                                    ))
                                    .child(
                                        div()
                                            .flex()
                                            .gap_2()
                                            .child(
                                                div()
                                                    .id("older-window")
                                                    .focusable()
                                                    .tab_stop(true)
                                                    .role(Role::Button)
                                                    .aria_label("Load older transcript window")
                                                    .px_2()
                                                    .py_1()
                                                    .rounded_md()
                                                    .bg(panel)
                                                    .cursor_pointer()
                                                    .on_click(cx.listener(|this, _, _, cx| {
                                                        this.shift_window(-1, cx)
                                                    }))
                                                    .child("Older"),
                                            )
                                            .child(
                                                div()
                                                    .id("newer-window")
                                                    .focusable()
                                                    .tab_stop(true)
                                                    .role(Role::Button)
                                                    .aria_label("Load newer transcript window")
                                                    .px_2()
                                                    .py_1()
                                                    .rounded_md()
                                                    .bg(panel)
                                                    .cursor_pointer()
                                                    .on_click(cx.listener(|this, _, _, cx| {
                                                        this.shift_window(1, cx)
                                                    }))
                                                    .child("Newer"),
                                            ),
                                    ),
                            )
                            .child(
                                list(self.list_state.clone(), move |index, _window, _cx| {
                                    let row = &rows[window_start + index];
                                    div()
                                        .id(("message", row.logical_index))
                                        .role(Role::ListItem)
                                        .aria_label(SharedString::from(format!(
                                            "{} message {}",
                                            row.kind, row.logical_index
                                        )))
                                        .h(px(row.height))
                                        .w_full()
                                        .px_4()
                                        .py_2()
                                        .border_b_1()
                                        .border_color(muted.opacity(0.18))
                                        .flex()
                                        .flex_col()
                                        .gap_1()
                                        .child(div().text_color(muted).text_xs().child(format!(
                                            "{} · #{}",
                                            row.kind, row.logical_index
                                        )))
                                        .child(row.body.clone())
                                        .into_any()
                                })
                                .flex_1()
                                .min_h_0(),
                            )
                            .child(
                                div()
                                    .flex_none()
                                    .p_3()
                                    .border_t_1()
                                    .border_color(muted.opacity(0.25))
                                    .child(
                                        div()
                                            .id("composer")
                                            .track_focus(&self.composer_focus)
                                            .focusable()
                                            .tab_stop(true)
                                            .role(Role::TextInput)
                                            .aria_label("Multiline composer prototype")
                                            .min_h(px(92.0))
                                            .max_h(px(170.0))
                                            .overflow_hidden()
                                            .p_3()
                                            .rounded_md()
                                            .border_1()
                                            .border_color(muted.opacity(0.45))
                                            .bg(panel)
                                            .cursor_text()
                                            .on_click(cx.listener(|this, _, window, cx| {
                                                window.focus(&this.composer_focus, cx);
                                            }))
                                            .on_key_down(cx.listener(|this, event, _, cx| {
                                                this.handle_composer_key(event, cx)
                                            }))
                                            .flex()
                                            .flex_col()
                                            .gap_1()
                                            .children(composer_lines.into_iter().enumerate().map(
                                                |(index, line)| {
                                                    div().id(("composer-line", index)).child(line)
                                                },
                                            )),
                                    ),
                            ),
                    )
                    .child(
                        div()
                            .w(px(self.dock_width))
                            .flex_none()
                            .p_3()
                            .border_l_1()
                            .border_color(muted.opacity(0.25))
                            .bg(panel)
                            .child(
                                div()
                                    .flex()
                                    .justify_between()
                                    .items_center()
                                    .mb_3()
                                    .child("Workspace dock")
                                    .child(
                                        div()
                                            .flex()
                                            .gap_1()
                                            .child(
                                                div()
                                                    .id("dock-narrower")
                                                    .focusable()
                                                    .tab_stop(true)
                                                    .role(Role::Button)
                                                    .aria_label("Make workspace dock narrower")
                                                    .px_2()
                                                    .py_1()
                                                    .cursor_pointer()
                                                    .on_click(cx.listener(|this, _, _, cx| {
                                                        this.dock_width =
                                                            (this.dock_width - 24.0).max(180.0);
                                                        cx.notify();
                                                    }))
                                                    .child("-"),
                                            )
                                            .child(
                                                div()
                                                    .id("dock-wider")
                                                    .focusable()
                                                    .tab_stop(true)
                                                    .role(Role::Button)
                                                    .aria_label("Make workspace dock wider")
                                                    .px_2()
                                                    .py_1()
                                                    .cursor_pointer()
                                                    .on_click(cx.listener(|this, _, _, cx| {
                                                        this.dock_width =
                                                            (this.dock_width + 24.0).min(480.0);
                                                        cx.notify();
                                                    }))
                                                    .child("+"),
                                            ),
                                    ),
                            )
                            .child(
                                div()
                                    .id("file-drop-target")
                                    .role(Role::Group)
                                    .aria_label("File drop target")
                                    .h(px(120.0))
                                    .p_3()
                                    .rounded_md()
                                    .border_1()
                                    .border_color(muted.opacity(0.45))
                                    .on_drop(cx.listener(|this, paths: &ExternalPaths, _, cx| {
                                        this.dropped_paths = paths.paths().to_vec();
                                        cx.notify();
                                    }))
                                    .child(drop_label),
                            )
                            .child(
                                div()
                                    .mt_3()
                                    .text_color(muted)
                                    .text_xs()
                                    .child(format!("dock width: {:.0}px", self.dock_width)),
                            ),
                    ),
            )
    }
}

fn main() {
    application().run(|cx: &mut App| {
        let bounds = Bounds::centered(None, size(px(1280.0), px(820.0)), cx);
        cx.open_window(
            WindowOptions {
                focus: true,
                window_bounds: Some(WindowBounds::Windowed(bounds)),
                titlebar: Some(gpui::TitlebarOptions {
                    title: Some("Chat On Steroids · GPUI feasibility".into()),
                    ..Default::default()
                }),
                ..Default::default()
            },
            |window, cx| cx.new(|cx| Prototype::new(window, cx)),
        )
        .expect("open GPUI feasibility window");
        cx.activate(true);
    });
}
