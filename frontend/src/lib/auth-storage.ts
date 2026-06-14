const ACCESS_KEY = "maintolio.access";
const REFRESH_KEY = "maintolio.refresh";
const ORG_KEY = "maintolio.organization";

export type StoredTokens = {
  access: string;
  refresh: string;
};

export function getTokens(): StoredTokens | null {
  if (typeof window === "undefined") return null;
  const access = window.localStorage.getItem(ACCESS_KEY);
  const refresh = window.localStorage.getItem(REFRESH_KEY);
  if (!access || !refresh) return null;
  return { access, refresh };
}

export function setTokens(tokens: StoredTokens) {
  window.localStorage.setItem(ACCESS_KEY, tokens.access);
  window.localStorage.setItem(REFRESH_KEY, tokens.refresh);
}

export function clearTokens() {
  window.localStorage.removeItem(ACCESS_KEY);
  window.localStorage.removeItem(REFRESH_KEY);
}

export function getSelectedOrganizationId() {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(ORG_KEY);
}

export function setSelectedOrganizationId(id: string | null) {
  if (!id) {
    window.localStorage.removeItem(ORG_KEY);
    return;
  }
  window.localStorage.setItem(ORG_KEY, id);
}

