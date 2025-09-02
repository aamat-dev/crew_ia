import * as React from 'react';

interface RunEvent {
  id: string;
  status: string;
  timestamp: string;
}

interface RunsTimelineProps {
  events: RunEvent[];
}

export function RunsTimeline({ events }: RunsTimelineProps) {
  return (
    <ol role="list" aria-label="Historique des runs" className="space-y-2">
      {events.map((event) => (
        <li
          key={event.id}
          role="listitem"
          aria-label={`${event.status} à ${event.timestamp}`}
          className="flex items-center space-x-2"
        >
          <span className="font-medium">{event.status}</span>
          <time className="text-sm text-muted-foreground">{event.timestamp}</time>
        </li>
      ))}
    </ol>
  );
}
