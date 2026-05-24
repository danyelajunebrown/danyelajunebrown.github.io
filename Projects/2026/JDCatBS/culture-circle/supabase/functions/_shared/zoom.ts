// Shared Zoom Server-to-Server OAuth helper.
// One Zoom account, no per-user OAuth dance: exchange the account credentials
// for a short-lived access token and call Zoom REST with it.

export async function getZoomToken(): Promise<string> {
  const accountId    = Deno.env.get('ZOOM_ACCOUNT_ID')
  const clientId     = Deno.env.get('ZOOM_CLIENT_ID')
  const clientSecret = Deno.env.get('ZOOM_CLIENT_SECRET')
  if (!accountId || !clientId || !clientSecret) {
    throw new Error('Missing ZOOM_ACCOUNT_ID / ZOOM_CLIENT_ID / ZOOM_CLIENT_SECRET')
  }

  const basic = btoa(`${clientId}:${clientSecret}`)
  const res = await fetch(
    `https://zoom.us/oauth/token?grant_type=account_credentials&account_id=${accountId}`,
    { method: 'POST', headers: { 'Authorization': `Basic ${basic}` } },
  )
  if (!res.ok) throw new Error(`Zoom token: ${res.status} ${await res.text()}`)
  const { access_token } = await res.json()
  return access_token
}

export async function zoomGet(path: string, token: string): Promise<any> {
  const res = await fetch(`https://api.zoom.us/v2${path}`, {
    headers: { 'Authorization': `Bearer ${token}` },
  })
  if (!res.ok) throw new Error(`Zoom GET ${path}: ${res.status} ${await res.text()}`)
  return res.json()
}
