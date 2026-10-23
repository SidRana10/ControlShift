"use client";

import { useEffect, useState } from "react";

/** True only after `active` has held for `ms`, so loading skeletons never flash on fast responses. */
export function useDelayedFlag(active: boolean, ms = 150): boolean {
  const [shown, setShown] = useState(false);
  useEffect(() => {
    const t = setTimeout(() => setShown(active), active ? ms : 0);
    return () => clearTimeout(t);
  }, [active, ms]);
  return active && shown;
}
