from django.http import JsonResponse
from django.shortcuts import render as django_render

from workflow import greet
from vercel.workflow import start, Run


def index(request):
    return django_render(request, "index.html")


async def trigger_workflow(request):
    name = request.GET.get("name", "World")
    run = await start(greet, name)
    return JsonResponse({"run_id": run.run_id, "name": name})


async def get_status(request, run_id):
    run = Run(run_id)
    status = await run.status()
    result = {"run_id": run_id, "status": status}
    if status == "completed":
        try:
            result["output"] = await run.return_value()
        except Exception as e:
            result["error"] = str(e)
    return JsonResponse(result)
