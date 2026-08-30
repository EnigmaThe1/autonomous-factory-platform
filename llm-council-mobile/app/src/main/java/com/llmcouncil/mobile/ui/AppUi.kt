package com.llmcouncil.mobile.ui

import android.content.Intent
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
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
import com.llmcouncil.mobile.BuildConfig
import com.llmcouncil.mobile.model.*
import java.text.DateFormat
import java.util.Date

private enum class Screen { HOME, MODELS, HISTORY, SETTINGS, LEARNING }

@Composable
fun CouncilApp(vm: AppViewModel) {
    var screen by remember { mutableStateOf(Screen.HOME) }
    var credentialSource by remember { mutableStateOf<ModelSource?>(null) }
    val run by vm.run.collectAsStateWithLifecycle()

    MaterialTheme(colorScheme = if (androidx.compose.foundation.isSystemInDarkTheme()) darkColorScheme() else lightColorScheme()) {
        Scaffold(
            topBar = {
                TopAppBar(
                    title = {
                        Column {
                            Text("LLM Council", fontWeight = FontWeight.Bold)
                            Text("Karpathy council · mobile ${BuildConfig.VERSION_NAME}", style = MaterialTheme.typography.labelSmall)
                        }
                    },
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
                    Screen.HOME -> HomeScreen(vm, run, onModels = { screen = Screen.MODELS }, onSettings = { screen = Screen.SETTINGS })
                    Screen.MODELS -> ModelsScreen(vm, onLearning = { vm.loadHealth(); screen = Screen.LEARNING })
                    Screen.HISTORY -> HistoryScreen(vm)
                    Screen.SETTINGS -> SettingsScreen(vm, onModels = { screen = Screen.MODELS }, onLearning = { vm.loadHealth(); screen = Screen.LEARNING }, onCredential = { credentialSource = it })
                    Screen.LEARNING -> LearningScreen(vm, onModels = { screen = Screen.MODELS })
                }
            }
        }
        credentialSource?.let { source -> ProviderKeyDialog(vm, source) { credentialSource = null } }
    }
}

@Composable
private fun HomeScreen(vm: AppViewModel, run: CouncilRun, onModels: () -> Unit, onSettings: () -> Unit) {
    var question by remember { mutableStateOf("") }
    val selectionVersion by vm.selectionVersion.collectAsStateWithLifecycle()
    val selected = remember(selectionVersion) { vm.selectedModels() }
    val chairman = remember(selectionVersion) { vm.chairman() }
    val running = run.stage in listOf(CouncilStage.STAGE1, CouncilStage.STAGE2, CouncilStage.STAGE3)
    val anyCredential = ModelSource.entries.any(vm::providerKeyConfigured)

    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item {
            ElevatedCard(Modifier.fillMaxWidth()) {
                Row(Modifier.padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Default.Groups, null)
                    Spacer(Modifier.width(10.dp))
                    Column(Modifier.weight(1f)) {
                        Text("${selected.size} council models", fontWeight = FontWeight.SemiBold)
                        Text("Chairman: $chairman", style = MaterialTheme.typography.bodySmall, maxLines = 1, overflow = TextOverflow.Ellipsis)
                        vm.activePreset()?.let { Text("Preset: $it", style = MaterialTheme.typography.labelSmall) }
                    }
                    TextButton(onClick = onModels) { Text("Change") }
                }
            }
        }
        if (!anyCredential) item {
            ElevatedCard(colors = CardDefaults.elevatedCardColors(containerColor = MaterialTheme.colorScheme.errorContainer)) {
                Row(Modifier.fillMaxWidth().padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Default.Key, null); Spacer(Modifier.width(8.dp)); Text("No provider credential configured", Modifier.weight(1f)); TextButton(onClick = onSettings) { Text("Settings") }
                }
            }
        }
        if (selected.size > 8) item { AssistChip(onClick = {}, leadingIcon = { Icon(Icons.Default.Warning, null) }, label = { Text("Large council: Stage 2 traffic grows quickly with ${selected.size} models") }) }
        item {
            OutlinedTextField(
                value = question, onValueChange = { question = it }, modifier = Modifier.fillMaxWidth(), minLines = 4, maxLines = 10,
                label = { Text("Ask the council anything") }, placeholder = { Text("Compare approaches, review code, research a decision…") }
            )
        }
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(onClick = { vm.runCouncil(question) }, enabled = question.isNotBlank() && !running && selected.size >= 2 && anyCredential, modifier = Modifier.weight(1f)) {
                    Icon(Icons.Default.PlayArrow, null); Spacer(Modifier.width(6.dp)); Text("Ask council")
                }
                if (running) OutlinedButton(onClick = vm::cancelRun) { Icon(Icons.Default.Stop, null); Spacer(Modifier.width(4.dp)); Text("Cancel") }
            }
        }
        if (run.question.isNotBlank()) {
            item { StageProgress(run) }
            if (run.stage1.isNotEmpty()) item { Stage1Card(run.stage1) }
            if (run.stage2.isNotEmpty()) item { Stage2Card(run.stage2, run.aggregate) }
            run.chairman?.let { item { ChairmanCard(it) } }
            if (run.errors.isNotEmpty()) item { ErrorsCard(run.errors) }
            if (run.stage in listOf(CouncilStage.COMPLETE, CouncilStage.ERROR, CouncilStage.CANCELLED)) item {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedButton(onClick = { vm.runCouncil(run.question) }) { Icon(Icons.Default.Refresh, null); Spacer(Modifier.width(4.dp)); Text("Retry") }
                    if (run.stage == CouncilStage.ERROR) Button(onClick = onModels) { Icon(Icons.Default.Hub, null); Spacer(Modifier.width(4.dp)); Text("Change models") }
                    TextButton(onClick = vm::clearRun) { Text("Clear") }
                }
            }
        }
    }
}

@Composable
private fun StageProgress(run: CouncilRun) {
    val active = when (run.stage) {
        CouncilStage.STAGE1 -> 1; CouncilStage.STAGE2 -> 2; CouncilStage.STAGE3, CouncilStage.COMPLETE -> 3
        CouncilStage.ERROR -> when { run.chairman != null -> 3; run.stage2.isNotEmpty() -> 2; run.stage1.isNotEmpty() -> 1; else -> 0 }
        CouncilStage.CANCELLED -> when { run.stage2.isNotEmpty() -> 2; run.stage1.isNotEmpty() -> 1; else -> 0 }
        else -> 0
    }
    val successes = run.stage1.count { it.error == null && it.text.isNotBlank() }
    val status = when (run.stage) {
        CouncilStage.STAGE1 -> "Stage 1 · collecting individual responses"
        CouncilStage.STAGE2 -> "Stage 2 · peer review in progress"
        CouncilStage.STAGE3 -> "Stage 3 · chairman synthesis in progress"
        CouncilStage.COMPLETE -> "Council complete"
        CouncilStage.ERROR -> if (run.stage1.isNotEmpty() && run.stage2.isEmpty()) "Stopped after Stage 1 · $successes/${run.stage1.size} models succeeded" else "Council stopped with an error"
        CouncilStage.CANCELLED -> "Council run cancelled"
        else -> "Ready"
    }
    ElevatedCard(Modifier.fillMaxWidth(), colors = if (run.stage == CouncilStage.ERROR) CardDefaults.elevatedCardColors(containerColor = MaterialTheme.colorScheme.errorContainer) else CardDefaults.elevatedCardColors()) {
        Column(Modifier.padding(14.dp)) {
            Text("Council progress", fontWeight = FontWeight.SemiBold); Text(status, style = MaterialTheme.typography.bodySmall); Spacer(Modifier.height(8.dp))
            LinearProgressIndicator(progress = { active / 3f }, modifier = Modifier.fillMaxWidth()); Spacer(Modifier.height(8.dp))
            Text("① Responses    ② Peer review    ③ Chairman", style = MaterialTheme.typography.bodySmall)
        }
    }
}

@Composable
private fun Stage1Card(answers: List<ModelAnswer>) {
    var stageExpanded by remember { mutableStateOf(true) }
    var expandedModels by remember { mutableStateOf(setOf<String>()) }
    ElevatedCard(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(14.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                val successes = answers.count { it.error == null && it.text.isNotBlank() }
                Text("Stage 1 · Individual answers ($successes/${answers.size})", fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f))
                IconButton(onClick = { stageExpanded = !stageExpanded }) { Icon(if (stageExpanded) Icons.Default.ExpandLess else Icons.Default.ExpandMore, if (stageExpanded) "Collapse stage" else "Expand stage") }
            }
            if (stageExpanded) answers.forEach { answer ->
                HorizontalDivider(Modifier.padding(vertical = 8.dp))
                val full = answer.model in expandedModels
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(if (answer.error == null) Icons.Default.CheckCircle else Icons.Default.Error, null)
                    Spacer(Modifier.width(8.dp)); Text(answer.model, fontWeight = FontWeight.SemiBold, modifier = Modifier.weight(1f)); Text("${answer.latencyMs / 1000.0}s", style = MaterialTheme.typography.labelSmall)
                }
                if (answer.error != null) {
                    Text(answer.error, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodyMedium)
                } else {
                    Spacer(Modifier.height(6.dp))
                    Text(answer.text, style = MaterialTheme.typography.bodyMedium, maxLines = if (full) Int.MAX_VALUE else 9, overflow = if (full) TextOverflow.Clip else TextOverflow.Ellipsis)
                    TextButton(onClick = { expandedModels = if (full) expandedModels - answer.model else expandedModels + answer.model }) {
                        Icon(if (full) Icons.Default.UnfoldLess else Icons.Default.UnfoldMore, null); Spacer(Modifier.width(4.dp)); Text(if (full) "Collapse answer" else "Show full answer")
                    }
                }
            }
        }
    }
}

@Composable
private fun Stage2Card(reviews: List<RankingReview>, aggregate: List<AggregateRank>) {
    var reviewsExpanded by remember { mutableStateOf(false) }
    var fullReviews by remember { mutableStateOf(setOf<String>()) }
    ElevatedCard(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(14.dp)) {
            Text("Stage 2 · Peer ranking", fontWeight = FontWeight.Bold)
            if (aggregate.isNotEmpty()) {
                Spacer(Modifier.height(8.dp)); Text("Aggregate ranking", fontWeight = FontWeight.SemiBold)
                aggregate.forEachIndexed { index, rank -> Text("${index + 1}. ${rank.model} · avg ${rank.averageRank} · ${rank.votes} votes", style = MaterialTheme.typography.bodySmall) }
            }
            TextButton(onClick = { reviewsExpanded = !reviewsExpanded }) { Text(if (reviewsExpanded) "Hide individual reviews" else "Show individual reviews") }
            if (reviewsExpanded) reviews.forEach { review ->
                HorizontalDivider(Modifier.padding(vertical = 6.dp)); Text(review.model, fontWeight = FontWeight.SemiBold)
                val full = review.model in fullReviews
                Text(review.error ?: review.text, color = if (review.error != null) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.onSurface, style = MaterialTheme.typography.bodySmall, maxLines = if (full) Int.MAX_VALUE else 8, overflow = if (full) TextOverflow.Clip else TextOverflow.Ellipsis)
                if (review.error == null) TextButton(onClick = { fullReviews = if (full) fullReviews - review.model else fullReviews + review.model }) { Text(if (full) "Collapse review" else "Show full review") }
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
                    TextButton(onClick = { context.startActivity(Intent.createChooser(Intent(Intent.ACTION_SEND).apply { type = "text/plain"; putExtra(Intent.EXTRA_TEXT, answer.text) }, "Share council answer")) }) { Icon(Icons.Default.Share, null); Text("Share") }
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
private fun ModelsScreen(vm: AppViewModel, onLearning: () -> Unit) {
    val models by vm.models.collectAsStateWithLifecycle()
    val loading by vm.modelsLoading.collectAsStateWithLifecycle()
    val error by vm.modelsError.collectAsStateWithLifecycle()
    val verification by vm.verificationStatus.collectAsStateWithLifecycle()
    val health by vm.health.collectAsStateWithLifecycle()
    val selectionVersion by vm.selectionVersion.collectAsStateWithLifecycle()
    val selected = remember(selectionVersion) { vm.selectedModels() }
    val chairman = remember(selectionVersion) { vm.chairman() }
    var search by remember { mutableStateOf("") }
    var provider by remember { mutableStateOf("All") }
    LaunchedEffect(Unit) { vm.loadModels(); vm.loadHealth() }
    val providers = remember(models) { listOf("All") + models.map { it.provider }.distinct().sorted() }
    val filtered = remember(models, search, provider) { models.filter { (provider == "All" || it.provider == provider) && (search.isBlank() || it.name.contains(search, true) || it.id.contains(search, true)) } }
    val freeCount = remember(models) { models.count(vm::isFreeCouncilEligible) }
    val healthMap = remember(health) { health.associateBy { it.modelKey } }

    Column(Modifier.fillMaxSize().padding(16.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) { Text("AI models", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold); Text("${selected.size} council members · chairman: $chairman", style = MaterialTheme.typography.bodySmall) }
            IconButton(onClick = onLearning) { Icon(Icons.Default.FactCheck, "Learning register") }
        }
        Text("Presets are generated from live provider catalogues. Free is empirically verified before use.", style = MaterialTheme.typography.labelSmall, modifier = Modifier.padding(top = 4.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(6.dp), modifier = Modifier.padding(top = 8.dp)) {
            AssistChip(onClick = { vm.applyPreset("Balanced") }, label = { Text("Balanced") }, leadingIcon = { Icon(Icons.Default.Balance, null) })
            AssistChip(onClick = { vm.applyPreset("Low cost") }, label = { Text("Low cost") }, leadingIcon = { Icon(Icons.Default.Savings, null) })
        }
        Row(horizontalArrangement = Arrangement.spacedBy(6.dp), modifier = Modifier.padding(bottom = 6.dp)) {
            AssistChip(onClick = { vm.applyPreset("Free") }, enabled = freeCount >= 2, label = { Text("Free ($freeCount)") }, leadingIcon = { Icon(Icons.Default.MoneyOff, null) })
            AssistChip(onClick = { vm.applyPreset("High-end") }, label = { Text("High-end") }, leadingIcon = { Icon(Icons.Default.WorkspacePremium, null) })
        }
        verification?.let { Text(it, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.primary, modifier = Modifier.padding(bottom = 6.dp)) }
        OutlinedTextField(search, { search = it }, modifier = Modifier.fillMaxWidth(), singleLine = true, leadingIcon = { Icon(Icons.Default.Search, null) }, label = { Text("Search models") }, trailingIcon = { IconButton(onClick = { vm.loadModels(true) }) { Icon(Icons.Default.Refresh, "Refresh") } })
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
                val h = healthMap[model.id]
                ElevatedCard(Modifier.fillMaxWidth()) {
                    Row(Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                        Checkbox(checked, onCheckedChange = { vm.toggleCouncilModel(model.id) })
                        Column(Modifier.weight(1f)) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Text(model.name, fontWeight = FontWeight.SemiBold, maxLines = 1, overflow = TextOverflow.Ellipsis, modifier = Modifier.weight(1f))
                                if (model.isFree) SuggestionChip(onClick = {}, label = { Text("FREE") })
                            }
                            Text("${model.source.displayName} · ${model.apiId}", style = MaterialTheme.typography.labelSmall, maxLines = 1, overflow = TextOverflow.Ellipsis)
                            val ctx = if (model.contextLength > 0) "${model.contextLength / 1000}k ctx" else "ctx n/a"
                            val price = if (model.pricingKnown) "in $${"%.2f".format(model.promptPricePerMillion)}/1M · out $${"%.2f".format(model.completionPricePerMillion)}/1M" else "pricing n/a"
                            Text("$ctx · $price", style = MaterialTheme.typography.labelSmall)
                            h?.let { Text(if (it.verifiedWorking) "✓ verified working · ${it.successes} success / ${it.failures} fail" else "⚠ last test failed · ${it.successes} success / ${it.failures} fail", style = MaterialTheme.typography.labelSmall, color = if (it.verifiedWorking) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.error) }
                        }
                        IconButton(onClick = { vm.setChairman(model.id) }) { Icon(if (chairman == model.id) Icons.Default.Star else Icons.Default.StarBorder, if (chairman == model.id) "Chairman" else "Make chairman") }
                    }
                }
            }
        }
        if (selected.size > 8) Text("Cost warning: peer-review traffic grows approximately with the square of council size.", color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
    }
}

@Composable
private fun LearningScreen(vm: AppViewModel, onModels: () -> Unit) {
    val health by vm.health.collectAsStateWithLifecycle()
    val verification by vm.verificationStatus.collectAsStateWithLifecycle()
    LaunchedEffect(Unit) { vm.loadHealth() }
    Column(Modifier.fillMaxSize().padding(16.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) { Text("Model Learning Register", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f)); IconButton(onClick = onModels) { Icon(Icons.Default.Hub, "Models") } }
        Text("Operational evidence from probes and real council calls. A model can be re-tested as provider availability changes.", style = MaterialTheme.typography.bodySmall)
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.padding(vertical = 10.dp)) {
            Button(onClick = vm::verifyFreeModels) { Icon(Icons.Default.FactCheck, null); Spacer(Modifier.width(4.dp)); Text("Verify free models") }
            OutlinedButton(onClick = vm::clearHealth) { Icon(Icons.Default.DeleteSweep, null); Text("Clear register") }
        }
        verification?.let { Text(it, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.primary, modifier = Modifier.padding(bottom = 8.dp)) }
        if (health.isEmpty()) Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) { Text("No model evidence recorded yet") }
        else LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            items(health, key = { it.modelKey }) { h ->
                ElevatedCard(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(12.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) { Icon(if (h.verifiedWorking) Icons.Default.CheckCircle else Icons.Default.Error, null); Spacer(Modifier.width(8.dp)); Text(h.modelKey, fontWeight = FontWeight.SemiBold, modifier = Modifier.weight(1f)); Text(h.lastStatus.uppercase(), style = MaterialTheme.typography.labelSmall) }
                        Text("${h.source.displayName} · successes ${h.successes} · failures ${h.failures} · consecutive failures ${h.consecutiveFailures}", style = MaterialTheme.typography.bodySmall)
                        if (h.lastTestedAt > 0) Text("Last tested: ${DateFormat.getDateTimeInstance().format(Date(h.lastTestedAt))}", style = MaterialTheme.typography.labelSmall)
                        h.lastError?.let { Text(it, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.error, maxLines = 5, overflow = TextOverflow.Ellipsis) }
                    }
                }
            }
        }
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
private fun SettingsScreen(vm: AppViewModel, onModels: () -> Unit, onLearning: () -> Unit, onCredential: (ModelSource) -> Unit) {
    var concurrency by remember { mutableFloatStateOf(vm.concurrency().toFloat()) }
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item { Text("Settings", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold) }
        item { Text("Provider credentials", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold) }
        items(ModelSource.entries) { source ->
            ElevatedCard(Modifier.fillMaxWidth().clickable { onCredential(source) }) {
                ListItem(headlineContent = { Text(source.displayName) }, supportingContent = { Text(if (vm.providerKeyConfigured(source)) "Credential stored securely with Android Keystore" else "Not configured") }, leadingContent = { Icon(Icons.Default.Key, null) }, trailingContent = { Icon(Icons.Default.ChevronRight, null) })
            }
        }
        item {
            ElevatedCard(colors = CardDefaults.elevatedCardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
                Column(Modifier.padding(14.dp)) {
                    Text("Consumer chat subscriptions", fontWeight = FontWeight.SemiBold)
                    Text("ChatGPT, Claude and Gemini consumer subscriptions are separate from their developer APIs. This app does not collect website passwords, browser cookies, ChatGPT session credentials, Claude subscription OAuth tokens or Gemini consumer-session tokens. Codex/Claude Code sign-ins are also not treated as reusable third-party app credentials.", style = MaterialTheme.typography.bodySmall)
                }
            }
        }
        item { ElevatedCard(Modifier.fillMaxWidth().clickable(onClick = onModels)) { ListItem(headlineContent = { Text("AI models") }, supportingContent = { Text("Council members, chairman, dynamic presets, merged provider catalogues") }, leadingContent = { Icon(Icons.Default.Hub, null) }) } }
        item { ElevatedCard(Modifier.fillMaxWidth().clickable(onClick = onLearning)) { ListItem(headlineContent = { Text("Model Learning Register") }, supportingContent = { Text("Verified working/failed models from probes and real runs") }, leadingContent = { Icon(Icons.Default.FactCheck, null) }) } }
        item { ElevatedCard(Modifier.fillMaxWidth()) { Column(Modifier.padding(16.dp)) { Text("Parallel requests: ${concurrency.toInt()}", fontWeight = FontWeight.SemiBold); Slider(value = concurrency, onValueChange = { concurrency = it }, onValueChangeFinished = { vm.setConcurrency(concurrency.toInt()) }, valueRange = 1f..12f, steps = 10); Text("Lower values reduce provider bursts and credit reservations; higher values complete large councils faster.", style = MaterialTheme.typography.bodySmall) } } }
        item { ElevatedCard(Modifier.fillMaxWidth()) { ListItem(headlineContent = { Text("LLM Council Mobile ${BuildConfig.VERSION_NAME}") }, supportingContent = { Text("Personal-use Android adaptation of karpathy/llm-council. Three-stage council logic retained; provider routing, empirical model verification, security and mobile UI added.") }, leadingContent = { Icon(Icons.Default.Info, null) }) } }
    }
}

@Composable
private fun ProviderKeyDialog(vm: AppViewModel, source: ModelSource, onDismiss: () -> Unit) {
    var key by remember(source) { mutableStateOf("") }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(source.displayName) },
        text = {
            Column {
                Text("Enter the developer credential for ${source.displayName}. It is encrypted using Android Keystore and is not included in the APK.")
                Spacer(Modifier.height(8.dp))
                OutlinedTextField(key, { key = it }, label = { Text("API key / auth key") }, visualTransformation = PasswordVisualTransformation(), singleLine = true)
                if (vm.providerKeyConfigured(source)) Text("A credential is already stored. Saving replaces it; saving an empty value is disabled.", style = MaterialTheme.typography.labelSmall, modifier = Modifier.padding(top = 6.dp))
            }
        },
        confirmButton = { Button(onClick = { vm.saveProviderKey(source, key); onDismiss() }, enabled = key.isNotBlank()) { Text("Save") } },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancel") } }
    )
}
