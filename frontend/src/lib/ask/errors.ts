import { ApiError } from "@/lib/api/client";

export interface AskErrorCopy {
  title: string;
  body: string;
  /** Backend error code, shown as a small mono caption for support. */
  code?: string;
}

/**
 * Actionable wording for every way POST /ask can fail. Raw backend messages (which can name a
 * provider and an HTTP status) are not shown; the stable `code` is.
 */
export function describeAskError(error: ApiError): AskErrorCopy {
  const code = error.code;
  switch (code) {
    case "invalid_request":
      return {
        title: "That question can’t be sent",
        body: "The API rejected the request. Questions must be between 1 and 2,000 characters and contain no control characters.",
        code,
      };
    case "request_timeout":
    case "provider_timeout":
    case "proxy_timeout":
      return {
        title: "The answer took too long",
        body: "The API did not finish within its time limit. Try again, or ask a narrower question.",
        code,
      };
    case "provider_not_configured":
      return {
        title: "No language model is configured",
        body: "The API cannot generate answers right now. Control Explorer still works without it.",
        code,
      };
    case "internal_error":
      return {
        title: "The API ran into an internal error",
        body: "The question was not answered. Try again; if it keeps failing, check the backend log.",
        code,
      };
    case "api_unreachable":
      return unreachable(code);
    default:
      break;
  }
  if (error.kind === "unreachable") return unreachable(code);
  if (error.kind === "timeout") {
    return {
      title: "The answer took too long",
      body: "No response arrived within two minutes. Try again, or ask a narrower question.",
    };
  }
  if (error.status === 502 || code?.startsWith("provider")) {
    return {
      title: "The language model provider returned an error",
      body: "Evidence was not turned into an answer. This is usually temporary, so try again shortly.",
      code,
    };
  }
  return {
    title: "The API returned a response ControlShift can’t read",
    body: "Nothing is shown rather than guessing at its meaning. Try again.",
    code,
  };
}

function unreachable(code?: string): AskErrorCopy {
  return {
    title: "ControlShift API is unreachable",
    body: "The question could not be sent. Check that the backend is running (controlshift-serve) and try again.",
    code,
  };
}
