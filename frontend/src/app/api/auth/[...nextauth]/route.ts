/** Auth.js route handler — exposes OAuth callback and session endpoints at /api/auth/*. */
import { handlers } from "../../../../../auth";

export const { GET, POST } = handlers;
