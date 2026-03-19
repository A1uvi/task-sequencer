interface Props {
  version: number
  className?: string
}

export function VersionTag({ version, className = '' }: Props) {
  return (
    <span
      className={`inline-flex items-center rounded-full bg-indigo-100 px-2 py-0.5 text-xs font-semibold text-indigo-700 ${className}`}
    >
      v{version}
    </span>
  )
}
