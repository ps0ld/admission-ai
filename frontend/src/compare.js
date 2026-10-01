// Tiny helper: compare list (max 4 college ids) kept in localStorage
const KEY = 'compare_ids'
export const getCompare = () => {
  try { return JSON.parse(localStorage.getItem(KEY)) || [] } catch { return [] }
}
export const setCompare = (ids) => localStorage.setItem(KEY, JSON.stringify(ids.slice(0, 4)))
export const toggleCompare = (id) => {
  const ids = getCompare()
  const next = ids.includes(id) ? ids.filter((i) => i !== id) : [...ids, id]
  if (next.length > 4) return { ids, error: 'Max 4 colleges compare kar sakte ho' }
  setCompare(next)
  return { ids: next }
}
