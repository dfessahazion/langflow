import { useNavigate } from "react-router-dom";
import {
  Card,
  CardContent,
  CardDescription,
  CardTitle,
} from "../../../../components/ui/card";
import useFlowsManagerStore from "../../../../stores/flowsManagerStore";

export default function NewFlowCardComponent() {
  const addFlow = useFlowsManagerStore((state) => state.addFlow);
  const navigate = useNavigate();
  return (
    <Card
      onClick={() => {
        addFlow(true).then((id) => {
          navigate("/flow/" + id);
        });
      }}
      className="h-64 w-80 cursor-pointer bg-background pt-4"
      data-testid="blank-flow"
    >
      <CardContent className="h-full w-full">
        <div className="flex h-full w-full flex-col items-center justify-center rounded-md bg-muted align-middle bg-dotted-spacing-6 bg-dotted-muted-foreground bg-dotted-radius-px"></div>
      </CardContent>
      <CardDescription className="px-6 pb-4">
        <CardTitle className="text-lg text-primary">Blank Flow</CardTitle>
      </CardDescription>
    </Card>
  );
}
