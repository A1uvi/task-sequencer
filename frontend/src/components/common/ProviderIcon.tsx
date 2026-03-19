interface Props {
  provider: string
  className?: string
}

const providerConfig: Record<string, { label: string; classes: string }> = {
  openai: { label: 'OpenAI', classes: 'bg-emerald-100 text-emerald-700' },
  anthropic: { label: 'Claude', classes: 'bg-orange-100 text-orange-700' },
  google: { label: 'Gemini', classes: 'bg-blue-100 text-blue-700' },
}

export function ProviderIcon({ provider, className = '' }: Props) {
  const normalized = provider.toLowerCase()
  const config = providerConfig[normalized] ?? {
    label: provider,
    classes: 'bg-gray-100 text-gray-700',
  }

  return (
    <span
      className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-semibold ${config.classes} ${className}`}
    >
      {config.label}
    </span>
  )
}
