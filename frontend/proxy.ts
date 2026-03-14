import { auth } from "./auth";
import type { ProxyConfig } from "next/server";

export default auth;

export const config: ProxyConfig = {
  matcher: [
    /*
     * Match all request paths except:
     * - api (NextAuth + future API routes handle their own auth)
     * - _next/static (static files)
     * - _next/image (image optimization)
     * - favicon.ico, sitemap.xml, robots.txt (metadata)
     */
    "/((?!api|_next/static|_next/image|favicon\\.ico|sitemap\\.xml|robots\\.txt).*)",
  ],
};
