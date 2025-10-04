from django.shortcuts import render, redirect
import matplotlib.pyplot as plt
import networkx as nx
import io, base64
from .forms import MatrixForm, CommentForm
from .models import Comment
from .utils import resolver_transporte


# Función para balancear oferta y demanda
def balance_problem(oferta, demanda):
    total_oferta = sum(oferta)
    total_demanda = sum(demanda)
    balance_msg = ""
    
    if total_oferta > total_demanda:
        demanda.append(total_oferta - total_demanda)  # columna ficticia
        balance_msg = f"Se añadió una columna ficticia de demanda: {total_oferta - total_demanda}"
    elif total_demanda > total_oferta:
        oferta.append(total_demanda - total_oferta)  # fila ficticia
        balance_msg = f"Se añadió una fila ficticia de oferta: {total_demanda - total_oferta}"
    
    return oferta, demanda, balance_msg


def transporte(request):
    if request.method == "POST":
        step = request.POST.get("step", "1")

        # --- Paso 1 ---
        if step == "1":
            form = MatrixForm(request.POST)
            if form.is_valid():
                origenes = form.cleaned_data["origenes"]
                destinos = form.cleaned_data["destinos"]

                origenes_list = list(range(origenes))
                destinos_list = list(range(destinos))

                return render(
                    request,
                    "problem_solver/transporte.html",
                    {
                        "step": 2,
                        "origenes": origenes,
                        "destinos": destinos,
                        "origenes_list": origenes_list,
                        "destinos_list": destinos_list,
                    },
                )
            return render(
                request, "problem_solver/transporte.html", {"form": form, "step": 1}
            )

        # --- Paso 2 ---
        elif step == "2":
            origenes = int(request.POST.get("origenes"))
            destinos = int(request.POST.get("destinos"))

            # Leer matriz de costos
            costos = []
            for i in range(origenes):
                fila = request.POST.getlist(f"costo_{i}[]")
                if len(fila) != destinos:
                    fila += ["0"] * (destinos - len(fila))
                costos.append([int(x) for x in fila])

            oferta = [int(x) for x in request.POST.getlist("oferta[]")]
            demanda = [int(x) for x in request.POST.getlist("demanda[]")]

            # Balancear problema
            oferta, demanda, balance_msg = balance_problem(oferta, demanda)

            # Ajustar matriz de costos si se añadió columna o fila ficticia
            if len(demanda) > len(costos[0]):
                for fila in costos:
                    fila.append(0)  # columna ficticia
            if len(oferta) > len(costos):
                costos.append([0] * len(demanda))  # fila ficticia

            proveedores = [f"P{i+1}" for i in range(len(oferta))]
            destinos_nombres = [f"D{j+1}" for j in range(len(demanda))]

            # Método Esquina Noroeste
            asignacion = [[0] * len(demanda) for _ in range(len(oferta))]
            oferta_rest = oferta.copy()
            demanda_rest = demanda.copy()

            i = j = 0
            while i < len(oferta) and j < len(demanda):
                flujo = min(oferta_rest[i], demanda_rest[j])
                asignacion[i][j] = flujo
                oferta_rest[i] -= flujo
                demanda_rest[j] -= flujo
                if oferta_rest[i] == 0:
                    i += 1
                elif demanda_rest[j] == 0:
                    j += 1

            # Datos para la tabla de asignaciones
            tabla_datos = []
            for i in range(len(oferta)):
                fila = {
                    "nombre": f"Planta {i+1}",
                    "valores": asignacion[i],
                    "oferta": oferta[i],
                }
                tabla_datos.append(fila)

            # Costo total y desglose
            costo_total = 0
            desglose_costos = []
            for i in range(len(oferta)):
                for j in range(len(demanda)):
                    if asignacion[i][j] > 0:
                        contribucion = costos[i][j] * asignacion[i][j]
                        costo_total += contribucion
                        desglose_costos.append({
                            "origen": f"P{i+1}",
                            "destino": f"D{j+1}",
                            "cantidad": asignacion[i][j],
                            "costo_unitario": costos[i][j],
                            "contribucion": contribucion,
                        })

            total_asignaciones = sum(sum(fila) for fila in asignacion)

            # Grafo
            G = nx.DiGraph()
            for p in proveedores:
                G.add_node(p, bipartite=0)
            for d in destinos_nombres:
                G.add_node(d, bipartite=1)
            for i, p in enumerate(proveedores):
                for j, d in enumerate(destinos_nombres):
                    if asignacion[i][j] > 0:
                        etiqueta = f"{asignacion[i][j]} @ {costos[i][j]}"
                        G.add_edge(p, d, label=etiqueta, weight=asignacion[i][j])

            pos = {}
            pos.update((p, (0, i)) for i, p in enumerate(proveedores))
            pos.update((d, (1, j)) for j, d in enumerate(destinos_nombres))

            fig, ax = plt.subplots(figsize=(8, 5))
            nx.draw(
                G,
                pos,
                with_labels=True,
                node_size=1500,
                node_color="skyblue",
                font_size=10,
                ax=ax,
                arrows=True,
                connectionstyle="arc3,rad=0.1",
            )
            labels = nx.get_edge_attributes(G, "label")
            nx.draw_networkx_edge_labels(G, pos, edge_labels=labels, font_size=9)

            buf = io.BytesIO()
            plt.tight_layout()
            plt.savefig(buf, format="png")
            buf.seek(0)
            grafica_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            plt.close(fig)

            destinos_range = range(len(demanda))

            return render(
                request,
                "problem_solver/result.html",
                {
                    "grafica": grafica_base64,
                    "resultado": "Solución usando el Método de la Esquina Noroeste",
                    "tabla_datos": tabla_datos,
                    "demanda": demanda,
                    "total_oferta": sum(oferta),
                    "total_demanda": sum(demanda),
                    "costo_total": costo_total,
                    "desglose_costos": desglose_costos,  # 👈 aquí va el detalle
                    "total_asignaciones": total_asignaciones,
                    "origenes": len(oferta),
                    "destinos": destinos_range,
                    "destinos_count": len(demanda),
                    "destinos_nombres": destinos_nombres,
                    "balance_msg": balance_msg,
                },
            )

    else:
        form = MatrixForm()
        return render(request, "problem_solver/transporte.html", {"form": form, "step": 1})


def home(request):
    return render(request, "problem_solver/home.html")


# -------------------------------
# NUEVAS VISTAS PARA COMENTARIOS
# -------------------------------
def add_comment(request):
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("comment_success")
    else:
        form = CommentForm()
    return render(request, "problem_solver/add_comment.html", {"form": form})


def comment_success(request):
    comments = Comment.objects.order_by("-created_at")
    return render(request, "problem_solver/comment_success.html", {"comments": comments})


def transporte_costo_minimo(request):
    if request.method == "POST":
        step = request.POST.get("step", "1")

        # --- Paso 1 ---
        if step == "1":
            form = MatrixForm(request.POST)
            if form.is_valid():
                origenes = form.cleaned_data["origenes"]
                destinos = form.cleaned_data["destinos"]

                origenes_list = list(range(origenes))
                destinos_list = list(range(destinos))

                return render(
                    request,
                    "problem_solver/transporte.html",
                    {
                        "step": 2,
                        "origenes": origenes,
                        "destinos": destinos,
                        "origenes_list": origenes_list,
                        "destinos_list": destinos_list,
                        "metodo": "Costo Mínimo",  # Indicamos método
                    },
                )
            return render(
                request, "problem_solver/transporte.html", {"form": form, "step": 1}
            )

        # --- Paso 2 ---
        elif step == "2":
            origenes = int(request.POST.get("origenes"))
            destinos = int(request.POST.get("destinos"))

            costos = []
            for i in range(origenes):
                fila = request.POST.getlist(f"costo_{i}[]")
                if len(fila) != destinos:
                    fila += ["0"] * (destinos - len(fila))
                costos.append([int(x) for x in fila])

            oferta = [int(x) for x in request.POST.getlist("oferta[]")]
            demanda = [int(x) for x in request.POST.getlist("demanda[]")]

            proveedores = [f"P{i+1}" for i in range(len(oferta))]
            destinos_nombres = [f"D{j+1}" for j in range(len(demanda))]

            resultado = resolver_transporte(costos, oferta, demanda, proveedores, destinos_nombres)

            # Crear grafo para visualización
            import networkx as nx
            fig, ax = plt.subplots(figsize=(8, 5))
            G = nx.DiGraph()
            for p in proveedores:
                G.add_node(p, bipartite=0)
            for d in destinos_nombres:
                G.add_node(d, bipartite=1)
            for dato in resultado["desglose_costos"]:
                G.add_edge(dato["origen"], dato["destino"], label=f"{dato['cantidad']} @ {dato['costo_unitario']}")
            pos = {}
            pos.update((p, (0, i)) for i, p in enumerate(proveedores))
            pos.update((d, (1, j)) for j, d in enumerate(destinos_nombres))
            nx.draw(
                G, pos,
                with_labels=True,
                node_size=1500,
                node_color="skyblue",
                font_size=10,
                ax=ax,
                arrows=True,
                connectionstyle="arc3,rad=0.1",
            )
            labels = nx.get_edge_attributes(G, "label")
            nx.draw_networkx_edge_labels(G, pos, edge_labels=labels, font_size=9)

            buf = io.BytesIO()
            plt.tight_layout()
            plt.savefig(buf, format="png")
            buf.seek(0)
            grafica_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            plt.close(fig)

            destinos_range = range(len(resultado["demanda"]))

            return render(
                request,
                "problem_solver/result.html",
                {
                    "grafica": grafica_base64,
                    "resultado": "Solución usando el Método de Costo Mínimo",
                    "tabla_datos": resultado["tabla_datos"],
                    "demanda": resultado["demanda"],
                    "total_oferta": resultado["total_oferta"],
                    "total_demanda": resultado["total_demanda"],
                    "costo_total": resultado["costo_total"],
                    "desglose_costos": resultado["desglose_costos"],
                    "total_asignaciones": sum(sum(f["valores"]) for f in resultado["tabla_datos"]),
                    "origenes": len(resultado["oferta"]),
                    "destinos": destinos_range,
                    "destinos_count": len(resultado["demanda"]),
                    "destinos_nombres": destinos_nombres,
                    "balance_msg": resultado["balance_msg"],
                },
            )

    else:
        form = MatrixForm()
        return render(request, "problem_solver/transporte.html", {"form": form, "step": 1})
