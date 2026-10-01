#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum TranscriptKind {
    User,
    Assistant,
    Tool,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct TranscriptRow {
    pub id: usize,
    pub kind: TranscriptKind,
    pub title: String,
    pub body: String,
}

pub fn synthetic_transcript_from(first_id: usize, count: usize) -> Vec<TranscriptRow> {
    (first_id..first_id + count)
        .map(|id| {
            let index = id - 1;
            let kind = match index % 5 {
                0 => TranscriptKind::User,
                1 | 2 | 3 => TranscriptKind::Assistant,
                _ => TranscriptKind::Tool,
            };

            let paragraph_count = 1 + (index % 5);
            let mut body = String::new();
            for paragraph in 0..paragraph_count {
                if paragraph > 0 {
                    body.push_str("\n\n");
                }
                body.push_str(match kind {
                    TranscriptKind::User => {
                        "Please inspect this synthetic task and preserve the exact session identity while updating the visible workspace."
                    }
                    TranscriptKind::Assistant => {
                        "This is deterministic fixture content used to exercise wrapping, variable row measurement, and virtualized transcript scrolling without touching production application state."
                    }
                    TranscriptKind::Tool => {
                        "tool_result: completed synthetic operation; owner=session-fixture; bytes=4096; status=ok"
                    }
                });
            }

            TranscriptRow {
                id,
                kind,
                title: match kind {
                    TranscriptKind::User => "User",
                    TranscriptKind::Assistant => "Assistant",
                    TranscriptKind::Tool => "Tool result",
                }
                .to_owned(),
                body,
            }
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fixture_ids_are_stable_and_unique() {
        let rows = synthetic_transcript_from(1, 10_000);

        assert_eq!(rows.len(), 10_000);
        assert_eq!(rows.first().map(|row| row.id), Some(1));
        assert_eq!(rows.last().map(|row| row.id), Some(10_000));
        assert!(rows.windows(2).all(|pair| pair[0].id + 1 == pair[1].id));
    }

    #[test]
    fn fixture_rows_have_variable_content_height_inputs() {
        let rows = synthetic_transcript_from(1, 10);
        let newline_counts: Vec<_> = rows
            .iter()
            .map(|row| row.body.matches("\n\n").count())
            .collect();

        assert!(newline_counts.iter().any(|count| *count == 0));
        assert!(newline_counts.iter().any(|count| *count >= 4));
    }
}
