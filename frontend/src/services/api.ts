export const API_BASE = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1').replace(/\/$/, '')
export function errorMessage(body: unknown): string {
  const detail = (body as { detail?: unknown })?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map(e => `${e.loc?.slice(1).join('.')}: ${e.msg}`).join('; ')
  return 'Request failed. Please try again.'
}
export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response: Response
  try { response = await fetch(`${API_BASE}${path}`, { ...init, headers: { 'Content-Type': 'application/json', ...init.headers } }) }
  catch (error) {
    if (init.signal?.aborted || (error instanceof DOMException && error.name === 'AbortError')) {
      throw new DOMException('The request was aborted.', 'AbortError')
    }
    throw new Error('Cannot reach StatCom backend. Check that the API is running.')
  }
  const body = await response.json().catch(() => null)
  if (!response.ok) throw new Error(errorMessage(body))
  return body as T
}
export async function allPages<T>(path: string): Promise<T[]> {
  const result: T[] = []
  for (let offset = 0; ; offset += 100) {
    const page = await api<T[]>(`${path}${path.includes('?') ? '&' : '?'}offset=${offset}&limit=100`)
    result.push(...page)
    if (page.length < 100) return result
  }
}
