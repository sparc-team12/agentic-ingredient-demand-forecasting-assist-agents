// `/chat-agent` stub route (ACRI-66) — protected by `RequireAuth` in
// `App.tsx`. Real business logic lands in a later, dedicated story.
import { StubScreen } from "@/components/common/stub-screen";
import { SCREENS } from "@/lib/screens";

const screen = SCREENS.find((s) => s.id === "chat-agent")!;

export default function ChatAgentRoute() {
  return <StubScreen screen={screen} />;
}
