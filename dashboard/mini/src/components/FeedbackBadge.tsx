import type { JSX } from 'react';
import type { Feedback } from '../api/types';
import { FEEDBACK_CRITICAL_THRESHOLD } from '../config/env';

interface Props {
  feedbacks?: Feedback[];
}

const FeedbackBadge = ({ feedbacks }: Props): JSX.Element | null => {
  if (!feedbacks || feedbacks.length === 0) return null;
  const sorted = [...feedbacks].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
  );
  const critical = sorted.find((f) => f.score < FEEDBACK_CRITICAL_THRESHOLD);
  const latest = sorted[0];
  const color = critical ? 'red' : '#ccc';
  const title = critical ? critical.comment : latest?.comment;
  return (
    <span
      data-testid="feedback-badge"
      title={title}
      style={{
        display: 'inline-block',
        width: 8,
        height: 8,
        borderRadius: '50%',
        background: color,
        marginLeft: 4,
      }}
    />
  );
};

export default FeedbackBadge;
