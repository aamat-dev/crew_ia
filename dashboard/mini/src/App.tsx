import ApiKeyBanner from "./components/ApiKeyBanner";
import { ApiKeyProvider } from "./state/ApiKeyContext";

export const App = (): JSX.Element => (
  <ApiKeyProvider>
    <div>
      <ApiKeyBanner />
    </div>
  </ApiKeyProvider>
);

export default App;
