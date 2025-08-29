import type { JSX } from 'react';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Status } from '../api/types';
import RunsTable from '../components/RunsTable';
import { useApiKey } from '../state/ApiKeyContext';
import useDebouncedValue from '../hooks/useDebouncedValue';

const RunsPage = (): JSX.Element => {
  const { apiKey, useEnvKey } = useApiKey();
  const hasKey = Boolean(apiKey) || useEnvKey;
  const navigate = useNavigate();

  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [status, setStatus] = useState<Status[]>([]);
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [titleInput, setTitleInput] = useState('');
  const [orderBy, setOrderBy] = useState('started_at');
  const [orderDir, setOrderDir] = useState<'asc' | 'desc'>('desc');

  const title = useDebouncedValue(titleInput, 300);

  const onOpenRun = (id: string): void => {
    navigate(`/runs/${id}`);
  };

  const resetFilters = (): void => {
    setPage(1);
    setPageSize(20);
    setStatus([]);
    setDateFrom('');
    setDateTo('');
    setTitleInput('');
  };

  useEffect(() => {
    setPage(1);
  }, [status, dateFrom, dateTo, title, orderBy, orderDir]);

  if (!hasKey) {
    return <div>Veuillez saisir une clé API pour continuer.</div>;
  }

  const toggleStatus = (s: Status): void => {
    setStatus((prev) =>
      prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s],
    );
  };

  return (
    <div>
      <div
        style={{
          border: '1px solid #ccc',
          padding: '8px',
          marginBottom: '16px',
        }}
      >
        <div style={{ marginBottom: '8px' }}>
          {(
            [
              'queued',
              'running',
              'succeeded',
              'failed',
              'canceled',
              'partial',
            ] as Status[]
          ).map((s) => (
            <label key={s} style={{ marginRight: '8px' }}>
              <input
                type="checkbox"
                checked={status.includes(s)}
                onChange={() => toggleStatus(s)}
              />
              {s}
            </label>
          ))}
        </div>
        <div style={{ marginBottom: '8px' }}>
          <label>
            Du{' '}
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
            />
          </label>
          <label style={{ marginLeft: '8px' }}>
            au{' '}
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
            />
          </label>
        </div>
        <div style={{ marginBottom: '8px' }}>
          <input
            type="text"
            placeholder="Titre"
            value={titleInput}
            onChange={(e) => setTitleInput(e.target.value)}
          />
        </div>
        <button onClick={resetFilters}>Réinitialiser</button>
      </div>
      <RunsTable
        page={page}
        pageSize={pageSize}
        status={status.length ? status : undefined}
        dateFrom={dateFrom || undefined}
        dateTo={dateTo || undefined}
        title={title || undefined}
        orderBy={orderBy}
        orderDir={orderDir}
        onPageChange={setPage}
        onPageSizeChange={(s) => {
          setPageSize(s);
          setPage(1);
        }}
        onOrderByChange={setOrderBy}
        onOrderDirChange={setOrderDir}
        onOpenRun={onOpenRun}
      />
    </div>
  );
};

export default RunsPage;
