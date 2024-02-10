import { useState } from "react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "../../../ui/dropdown-menu";

import { useNavigate } from "react-router-dom";
import FlowSettingsModal from "../../../../modals/flowSettingsModal";
import useAlertStore from "../../../../stores/alertStore";
import useFlowStore from "../../../../stores/flowStore";
import useFlowsManagerStore from "../../../../stores/flowsManagerStore";
import IconComponent from "../../../genericIconComponent";
import { Button } from "../../../ui/button";

export const MenuBar = (): JSX.Element => {
  const addFlow = useFlowsManagerStore((state) => state.addFlow);
  const currentFlow = useFlowsManagerStore((state) => state.currentFlow);
  const setErrorData = useAlertStore((state) => state.setErrorData);
  const undo = useFlowsManagerStore((state) => state.undo);
  const redo = useFlowsManagerStore((state) => state.redo);
  const sidebarOpen = useFlowStore((state) => state.sidebarOpen);
  const setSidebarOpen = useFlowStore((state) => state.setSidebarOpen);
  const [openSettings, setOpenSettings] = useState(false);

  const navigate = useNavigate();

  function handleAddFlow() {
    try {
      addFlow(true).then((id) => {
        navigate("/flow/" + id);
      });
      // saveFlowStyleInDataBase();
    } catch (err) {
      setErrorData(err as { title: string; list?: Array<string> });
    }
  }

  return currentFlow ? (
    <div className="ml-3 flex items-center gap-2">
      <Button
        variant="primary"
        size="sm"
        onClick={() => {
          setSidebarOpen(!sidebarOpen);
        }}
      >
        <IconComponent
          name={sidebarOpen ? "PanelRightOpen" : "PanelRightClose"}
          className="h-4 w-4"
        />
      </Button>
      <div className="flex items-center gap-0.5 rounded-md py-1 text-sm font-medium">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button asChild variant="primary" size="sm">
              <div className="header-menu-bar-display">
                <div className="header-menu-flow-name">{currentFlow.name}</div>
                <IconComponent name="ChevronDown" className="h-4 w-4" />
              </div>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-44">
            <DropdownMenuLabel>Options</DropdownMenuLabel>
            <DropdownMenuItem
              onClick={() => {
                handleAddFlow();
              }}
              className="cursor-pointer"
            >
              <IconComponent name="Plus" className="header-menu-options" />
              New
            </DropdownMenuItem>

            <DropdownMenuItem
              onClick={() => {
                setOpenSettings(true);
              }}
              className="cursor-pointer"
            >
              <IconComponent
                name="Settings2"
                className="header-menu-options "
              />
              Settings
            </DropdownMenuItem>

            <DropdownMenuItem
              onClick={() => {
                undo();
              }}
              className="cursor-pointer"
            >
              <IconComponent name="Undo" className="header-menu-options " />
              Undo
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={() => {
                redo();
              }}
              className="cursor-pointer"
            >
              <IconComponent name="Redo" className="header-menu-options " />
              Redo
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
        <FlowSettingsModal
          open={openSettings}
          setOpen={setOpenSettings}
        ></FlowSettingsModal>
      </div>
    </div>
  ) : (
    <></>
  );
};

export default MenuBar;
