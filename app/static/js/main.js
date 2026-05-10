// main.js — Shared JavaScript utilities for DocExtractor

// Convert "invoice_no" → "Invoice No"
function formatFieldName(key) {
  return key.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
}

// Format a value for display (handles null, numbers, etc.)
function formatValue(val) {
  if (val === null || val === undefined) return "—";
  if (typeof val === "number")           return val.toLocaleString();
  if (typeof val === "object")           return JSON.stringify(val);
  return String(val);
}
