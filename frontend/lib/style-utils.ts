/**
 * Returns the Tailwind CSS classes for a status badge based on the status string.
 * This ensures consistent styling for statuses across the application.
 * Colors are semantic for better user understanding.
 */
export const getStatusBadgeClasses = (status?: string | null): string => {
  switch (status?.trim()?.toLowerCase()) {
    case "completed":
    case "analyzed":
      return "bg-green-100 text-green-800 border-green-200 dark:bg-green-900/40 dark:text-green-300 dark:border-green-800";
    case "processing":
    case "in-progress":
    case "pending":
      return "bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-900/40 dark:text-blue-300 dark:border-blue-800";
    case "failed":
      return "bg-red-100 text-red-800 border-red-200 dark:bg-red-900/40 dark:text-red-300 dark:border-red-800";
    case "draft":
    default:
      console.warn(`[getStatusBadgeClasses] Unrecognized status: "${status}" (normalized: "${normalizedStatus}"). Falling back to default styling.`);
      return "bg-muted text-muted-foreground border-border";
  }
};
