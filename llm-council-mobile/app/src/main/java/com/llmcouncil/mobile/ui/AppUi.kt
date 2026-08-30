package com.llmcouncil.mobile.ui

import android.content.Intent
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.llmcouncil.mobile.AppViewModel
import com.llmcouncil.mobile.model.*
import java.text.DateFormat
import java.util.Date

private enum class Screen { HOME, MODELS, HISTORY, SETTINGS }

@Composable
fun CouncilApp(vm: AppViewModel) {
    var screen by remember { mutableStateOf(Screen.HOME) }
    var apiDialog by remember { mutableStateOf(!vm.hasApiKey()) }
    val run by vm.run.collectAsStateWithLifecycle()
    MaterialTheme(colorScheme = if (androidx.compose.foundation.isSystemInDarkTheme()) darkColorScheme() else lightColorScheme()) {
        Scaffold(
            topBar = {
                TopAppBar(
                    title = { Column { Text("LLM Council", fontWeight = FontWeight.Bold); Text("Karpathy council · mobile v4", style = MaterialTheme.typography.labelSmall) } },
                    actions = { IconButton(onClick = { screen = Screen.SETTINGS }) { Icon(Icons.Default.Settings, "Settings") } }
                )
            },
            bottomBar = {
                NavigationBar {
                    NavigationBarItem(selected = screen == Screen.HOME, onClick = { screen = Screen.HOME }, icon = { Icon(Icons.Default.Chat, null) }, label = { Text("Council") })
                    NavigationBarItem(selected = screen == Screen.MODELS, onClick = { screen = Screen.MODELS }, icon = { Icon(Icons.Default.Hub, null) }, label = { Text("Models") })
                    NavigationBarItem(selected = screen == Screen.HISTORY, onClick = { vm.loadHistory(); screen = Screen.HISTORY }, icon = { Icon(Icons.Default.History, null) }, label = { Text("History") })
                }
            }
        ) { pad ->
            Box(Modifier.padding(pad).fillMaxSize()) {
                when (screen) {
                    Screen.HOME -> HomeScreen(vm, run, onNeedKey = { apiDialog = true }, onModels = { screen = Screen.MODELS })
                    Screen.MODELS -> ModelsScreen(vm)
                    Screen.HISTORY -> HistoryScreen(vm)
                    Screen.SETTINGS -> SettingsScreen(vm, onApiKey = { apiDialog = true }, onModels = { screen = Screen.MODELS })
                }
            }
        }
        if (apiDialog) ApiKeyDialog(vm, required = !vm.hasApiKey(), onDismiss = { apiDialog = false })
    }
}

@Composable
private fun HomeScreen(vm: AppViewModel, run: CouncilRun, onNeedKey: () -> Unit, onModels: () -> Unit) {
    var question by remember { mutableStateOf("") }
    val selected = vm.selectedModels()
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        item {
            ElevatedCard(Modifier.fillMaxWidth()) {
                Row(Modifier.padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Default.Groups, null)
                    Spacer(Modifier.width(10.dp))
                    Column(Modifier.weight(1f)) {
                        Text("${selected.size} council models", fontWeight = FontWeight.SemiBold)
                        Text("Chairman: ${vm.chairman()}", style = MaterialTheme.typography.bodySmall, maxLines = 1, overflow = TextOverflow.Ellipsis)
                    }
                    TextButton(onClick = onModels) { Text("Change") }
                }
            }
        }
        if (selected.size > 8) item {
            AssistChip(onClick = {}, leadingIcon = { Icon(Icons.Default.Warning, null) }, label = { Text("Large council: Stage 2 cost grows quickly with ${selected.size} models") })
        }
        item {
            OutlinedTextField(
                value = question,
                onValueChange = { question = it },
                modifier = Modifier.fillMaxWidth(),
                minLines = 4,
                maxLines = 9,
                label = { Text("Ask the council anything") },
                placeholder = { Text("Compare approaches, review code, research a decision…") }
            )
        }
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(
                    onClick = { if (vm.hasApiKey()) vm.runCouncil(question) else onNeedKey() },
                    enabled = question.isNotBlank() && run.stage !in listOf(CouncilStage.STAGE1, CouncilStage.STAGE2, CouncilStage.STAGE3),
                    modifier = Modifier.weight(1f)
                ) { Icon(Icons.Default.PlayArrow, null); Spacer(Modifier.width(6.dp)); Text("Ask council") }
                if (run.stage in listOf(CouncilStage.STAGE1, CouncilStage.STAGE2, CouncilStage.STAGE3)) {
                    OutlinedButton(onClick = vm::cancelRun) { Icon(Icons.Default.Stop, null); Text("Cancel") }
                }
            }
        }
        if (run.question.isNotBlank()) {
            item { StageProgress(run.stage) }
            if (run.stage1.isNotEmpty()) item { Stage1Card(run.stage1) }
            if (run.stage2.isNotEmpty()) item { Stage2Card(run.stage2, run.aggregate) }
            run.chairman?.let { item { ChairmanCard(it) } }
            if (run.errors.isNotEmpty()) item { ErrorsCard(run.errors) }
            if (run.stage in listOf(CouncilStage.COMPLETE, CouncilStage.ERROR, CouncilStage.CANCELLED)) item {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedButton(onClick = { vm.runCouncil(run.question) }) { Icon(Icons.Default.Refresh, null); Text("Run again") }
                    TextButton(onClick = vm::clearRun) { Text("Clear") }
                }
            }
        }
    }
}

@Composable
private fun StageProgress(stage: CouncilStage) {
    val active = when (stage) { CouncilStage.STAGE1 -> 1; CouncilStage.STAGE2 -> 2; CouncilStage.STAGE3 -> 3; CouncilStage.COMPLETE -> 4; else -> 0 }
    ElevatedCard(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(14.dp)) {
            Text("Council progress", fontWeight = FontWeight.SemiBold)
            Spacer(Modifier.height(8.dp))
            LinearProgressIndicator(progress = { (active.coerceAtMost(3) / 3f) }, modifier = Modifier.fillMaxWidth())
            Spacer(Modifier.height(8.dp))
            Text("① Responses    ② Peer review    ③ Chairman", style = MaterialTheme.typography.bodySmall)
        }
    }
}

@Composable
private fun Stage1Card(answers: List<ModelAnswer>) {
    var expanded by remember { mutableStateOf(true) }
    ElevatedCard(Modifier.fillMaxWidth().clickable { expanded = !expanded }) {
        Column(Modifier.padding(14.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) { Text("Stage 1 · Individual answers", fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f)); Icon(if (expanded) Icons.Default.ExpandLess else Icons.Default.ExpandMore, null) }
            if (expanded) answers.forEach { a ->
                HorizontalDivider(Modifier.padding(vertical = 8.dp))
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(if (a.error == null) Icons.Default.CheckCircle else Icons.Default.Error, null)
                    Spacer(Modifier.width(8.dp)); Text(a.model, fontWeight = FontWeight.SemiBold, modifier = Modifier.weight(1f))
                    Text("${a.latencyMs / 1000.0}s", style = MaterialTheme.typography.labelSmall)
                }
                Text(if (a.error == null) a.text else a.error, style = MaterialTheme.typography.bodyMedium, maxLines = 10, overflow = TextOverflow.Ellipsis)
            }
        }
    }
}

@Composable
private fun Stage2Card(reviews: List<RankingReview>, aggregate: List<AggregateRank>) {
    var reviewsExpanded by remember { mutableStateOf(false) }
    ElevatedCard(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(14.dp)) {
            Text("Stage 2 · Peer ranking", fontWeight = FontWeight.Bold)
            if (aggregate.isNotEmpty()) {
                Spacer(Modifier.height(8.dp)); Text("Aggregate ranking", fontWeight = FontWeight.SemiBold)
                aggregate.forEachIndexed { index, rank -> Text("${index + 1}. ${rank.model}  ·  avg ${rank.averageRank}  ·  ${rank.votes} votes", style = MaterialTheme.typography.bodySmall) }
            }
            TextButton(onClick = { reviewsExpanded = !reviewsExpanded }) { Text(if (reviewsExpanded) "Hide individual reviews" else "Show individual reviews") }
            if (reviewsExpanded) reviews.forEach { r ->
                HorizontalDivider(Modifier.padding(vertical = 6.dp)); Text(r.model, fontWeight = FontWeight.SemiBold)
                Text(r.error ?: r.text, style = MaterialTheme.typography.bodySmall, maxLines = 8, overflow = TextOverflow.Ellipsis)
            }
        }
    }
}

@Composable
private fun ChairmanCard(answer: ModelAnswer) {
    val clipboard = LocalClipboardManager.current
    val context = LocalContext.current
    ElevatedCard(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) { Icon(Icons.Default.WorkspacePremium, null); Spacer(Modifier.width(8.dp)); Column { Text("Stage 3 · Chairman", fontWeight = FontWeight.Bold); Text(answer.model, style = MaterialTheme.typography.labelMedium) } }
            Spacer(Modifier.height(12.dp)); Text(answer.error ?: answer.text)
            if (answer.error == null) {
                Spacer(Modifier.height(10.dp)); Row {
                    TextButton(onClick = { clipboard.setText(AnnotatedString(answer.text)) }) { Icon(Icons.Default.ContentCopy, null); Text("Copy") }
                    TextButton(onClick = {
                        context.startActivity(Intent.createChooser(Intent(Intent.ACTION_SEND).apply { type = "text/plain"; putExtra(Intent.EXTRA_TEXT, answer.text) }, "Share council answer"))
                    }) { Icon(Icons.Default.Share, null); Text("Share") }
                }
            }
        }
    }
}

@Composable
private fun ErrorsCard(errors: Map<String, String>) {
    ElevatedCard(Modifier.fillMaxWidth(), colors = CardDefaults.elevatedCardColors(containerColor = MaterialTheme.colorScheme.errorContainer)) {
        Column(Modifier.padding(14.dp)) { Text("Run diagnostics", fontWeight = FontWeight.Bold); errors.forEach { (model, error) -> Text("• $model: $error", style = MaterialTheme.typography.bodySmall) } }
    }
}

@Composable
private fun ModelsScreen(vm: AppViewModel) {
    val models by vm.models.collectAsStateWithLifecycle()
    val loading by vm.modelsLoading.collectAsStateWithLifecycle()
    val error by vm.modelsError.collectAsStateWithLifecycle()
    var search by remember { mutableStateOf("") }
    var provider by remember { mutableStateOf("All") }
    var selected by remember { mutableStateOf(vm.selectedModels()) }
    var chairman by remember { mutableStateOf(vm.chairman()) }
    LaunchedEffect(Unit) { vm.loadModels() }
    val providers = remember(models) { listOf("All") + models.map { it.provider }.distinct().sorted() }
    val filtered = remember(models, search, provider) { models.filter { (provider == "All" || it.provider == provider) && (search.isBlank() || it.name.contains(search, true) || it.id.contains(search, true)) } }

    Column(Modifier.fillMaxSize().padding(16.dp)) {
        Text("AI models", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
        Text("${selected.size} council members · chairman: $chairman", style = MaterialTheme.typography.bodySmall)
        Row(horizontalArrangement = Arrangement.spacedBy(6.dp), modifier = Modifier.padding(vertical = 8.dp)) {
            AssistChip(onClick = { vm.applyPreset("Balanced"); selected = vm.selectedModels(); chairman = vm.chairman() }, label = { Text("Balanced") })
            AssistChip(onClick = { vm.applyPreset("Low cost"); selected = vm.selectedModels(); chairman = vm.chairman() }, label = { Text("Low cost") })
            AssistChip(onClick = { vm.applyPreset("Original"); selected = vm.selectedModels(); chairman = vm.chairman() }, label = { Text("Original") })
        }
        OutlinedTextField(search, { search = it }, modifier = Modifier.fillMaxWidth(), singleLine = true, leadingIcon = { Icon(Icons.Default.Search, null) }, label = { Text("Search OpenRouter models") }, trailingIcon = { IconButton(onClick = { vm.loadModels(true) }) { Icon(Icons.Default.Refresh, "Refresh") } })
        Spacer(Modifier.height(8.dp))
        if (providers.size > 1) {
            var expanded by remember { mutableStateOf(false) }
            Box { OutlinedButton(onClick = { expanded = true }) { Text("Provider: $provider"); Icon(Icons.Default.ArrowDropDown, null) }; DropdownMenu(expanded, { expanded = false }) { providers.forEach { p -> DropdownMenuItem(text = { Text(p) }, onClick = { provider = p; expanded = false }) } } }
        }
        if (loading) LinearProgressIndicator(Modifier.fillMaxWidth().padding(vertical = 8.dp))
        error?.let { Text(it, color = MaterialTheme.colorScheme.error, modifier = Modifier.padding(8.dp)) }
        LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.weight(1f)) {
            items(filtered, key = { it.id }) { model ->
                val checked = model.id in selected
                ElevatedCard(Modifier.fillMaxWidth()) {
                    Row(Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                        Checkbox(checked, onCheckedChange = { vm.toggleCouncilModel(model.id); selected = vm.selectedModels() })
                        Column(Modifier.weight(1f)) {
                            Text(model.name, fontWeight = FontWeight.SemiBold, maxLines = 1, overflow = TextOverflow.Ellipsis)
                            Text(model.id, style = MaterialTheme.typography.labelSmall, maxLines = 1, overflow = TextOverflow.Ellipsis)
                            val ctx = if (model.contextLength > 0) "${model.contextLength / 1000}k ctx" else "ctx n/a"
                            Text("$ctx · in $${"%.2f".format(model.promptPricePerMillion)}/1M · out $${"%.2f".format(model.completionPricePerMillion)}/1M", style = MaterialTheme.typography.labelSmall)
                        }
                        IconButton(onClick = { vm.setChairman(model.id); chairman = model.id }) { Icon(if (chairman == model.id) Icons.Default.Star else Icons.Default.StarBorder, if (chairman == model.id) "Chairman" else "Make chairman") }
                    }
                }
            }
        }
        if (selected.size > 8) Text("Cost warning: peer-review traffic grows approximately with the square of council size.", color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
    }
}

@Composable
private fun HistoryScreen(vm: AppViewModel) {
    val history by vm.history.collectAsStateWithLifecycle()
    var selected by remember { mutableStateOf<HistoryItem?>(null) }
    LaunchedEffect(Unit) { vm.loadHistory() }
    Column(Modifier.fillMaxSize().padding(16.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) { Text("History", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f)); if (history.isNotEmpty()) TextButton(onClick = vm::clearHistory) { Text("Clear all") } }
        if (history.isEmpty()) Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) { Text("No saved council runs yet") }
        else LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) { items(history, key = { it.id }) { item -> ElevatedCard(Modifier.fillMaxWidth().clickable { selected = item }) { Column(Modifier.padding(14.dp)) { Text(item.title, fontWeight = FontWeight.SemiBold); Text(DateFormat.getDateTimeInstance().format(Date(item.createdAt)), style = MaterialTheme.typography.labelSmall); Text(item.question, maxLines = 2, overflow = TextOverflow.Ellipsis) } } } }
    }
    selected?.let { item -> AlertDialog(onDismissRequest = { selected = null }, title = { Text(item.title) }, text = { LazyColumn { item { Text("Question", fontWeight = FontWeight.Bold); Text(item.question); Spacer(Modifier.height(12.dp)); Text("Chairman · ${item.chairman}", fontWeight = FontWeight.Bold); Text(item.finalAnswer) } } }, confirmButton = { TextButton(onClick = { selected = null }) { Text("Close") } }) }
}

@Composable
private fun SettingsScreen(vm: AppViewModel, onApiKey: () -> Unit, onModels: () -> Unit) {
    var concurrency by remember { mutableFloatStateOf(vm.concurrency().toFloat()) }
    Column(Modifier.fillMaxSize().padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Text("Settings", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
        ElevatedCard(Modifier.fillMaxWidth().clickable(onClick = onApiKey)) { ListItem(headlineContent = { Text("OpenRouter API key") }, supportingContent = { Text(if (vm.hasApiKey()) "Stored securely with Android Keystore" else "Not configured") }, leadingContent = { Icon(Icons.Default.Key, null) }) }
        ElevatedCard(Modifier.fillMaxWidth().clickable(onClick = onModels)) { ListItem(headlineContent = { Text("AI models") }, supportingContent = { Text("Council members, chairman, live OpenRouter catalogue") }, leadingContent = { Icon(Icons.Default.Hub, null) }) }
        ElevatedCard(Modifier.fillMaxWidth()) { Column(Modifier.padding(16.dp)) { Text("Parallel requests: ${concurrency.toInt()}", fontWeight = FontWeight.SemiBold); Slider(value = concurrency, onValueChange = { concurrency = it }, onValueChangeFinished = { vm.setConcurrency(concurrency.toInt()) }, valueRange = 1f..12f, steps = 10); Text("Lower values reduce provider bursts; higher values complete large councils faster.", style = MaterialTheme.typography.bodySmall) } }
        ElevatedCard(Modifier.fillMaxWidth()) { ListItem(headlineContent = { Text("LLM Council Mobile v4") }, supportingContent = { Text("Personal-use Android adaptation of karpathy/llm-council. Three-stage council logic retained; mobile orchestration, security and UI modernised.") }, leadingContent = { Icon(Icons.Default.Info, null) }) }
    }
}

@Composable
private fun ApiKeyDialog(vm: AppViewModel, required: Boolean, onDismiss: () -> Unit) {
    var key by remember { mutableStateOf("") }
    AlertDialog(
        onDismissRequest = { if (!required) onDismiss() },
        title = { Text("OpenRouter API key") },
        text = { Column { Text("Your key is encrypted with Android Keystore and is not included in the APK."); Spacer(Modifier.height(8.dp)); OutlinedTextField(key, { key = it }, label = { Text("sk-or-v1-…") }, visualTransformation = PasswordVisualTransformation(), singleLine = true) } },
        confirmButton = { Button(onClick = { if (key.isNotBlank()) { vm.saveApiKey(key); onDismiss() } }, enabled = key.isNotBlank()) { Text("Save") } },
        dismissButton = { if (!required) TextButton(onClick = onDismiss) { Text("Cancel") } }
    )
}
