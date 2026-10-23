"use client";

import { useSyncExternalStore } from "react";
import { createPortal } from "react-dom";

export const HEADER_ACTIONS_ID = "page-header-actions";

const subscribe = () => () => {};

/** Renders page-scoped controls into the shell header's right-hand slot (spec section 4). */
export function HeaderActions({ children }: { children: React.ReactNode }) {
  const slot = useSyncExternalStore(
    subscribe,
    () => document.getElementById(HEADER_ACTIONS_ID),
    () => null,
  );
  return slot ? createPortal(children, slot) : null;
}
