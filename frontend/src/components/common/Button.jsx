import Spinner from './Spinner';

export default function Button({
  children,
  onClick,
  variant = 'primary',   // 'primary' | 'ghost' | 'danger'
  size = 'md',           // 'sm' | 'md'
  loading = false,
  disabled = false,
  type = 'button',
  style,
}) {
  const base = {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '6px',
    border: 'none',
    borderRadius: 'var(--radius)',
    cursor: disabled || loading ? 'not-allowed' : 'pointer',
    fontFamily: 'inherit',
    fontWeight: 500,
    transition: 'background 0.15s, opacity 0.15s',
    opacity: disabled || loading ? 0.5 : 1,
    padding: size === 'sm' ? '4px 10px' : '7px 14px',
    fontSize: size === 'sm' ? '12px' : '13px',
  };

  const variants = {
    primary: {
      background: 'var(--accent)',
      color: '#fff',
    },
    ghost: {
      background: 'transparent',
      color: 'var(--text-secondary)',
      border: '1px solid var(--border-light)',
    },
    danger: {
      background: 'var(--error-dim)',
      color: 'var(--error)',
      border: '1px solid rgba(239,68,68,0.25)',
    },
  };

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      style={{ ...base, ...variants[variant], ...style }}
    >
      {loading && <Spinner size={13} />}
      {children}
    </button>
  );
}
