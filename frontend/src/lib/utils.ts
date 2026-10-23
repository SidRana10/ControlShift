import { clsx, type ClassValue } from "clsx";
import { extendTailwindMerge } from "tailwind-merge";

/**
 * Class merging that knows the design system's custom font-size utilities (text-ui, text-label…).
 * Without this, tailwind-merge mistakes them for colours and drops them next to a text-fg-* class.
 */
const twMerge = extendTailwindMerge({
  extend: {
    classGroups: {
      "font-size": [
        {
          text: [
            "label",
            "caption",
            "ui-sm",
            "ui",
            "body",
            "title-sm",
            "title",
            "name-lg",
            "id",
            "id-lg",
            "source",
            "source-lg",
          ],
        },
      ],
    },
  },
});

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
