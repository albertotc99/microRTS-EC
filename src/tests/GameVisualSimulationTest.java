/*
* To change this template, choose Tools | Templates
* and open the template in the editor.
*/
package tests;

import ai.core.AI;
import ai.machinelearning.bayes.CalibratedNaiveBayes;
import ai.mcts.believestatemcts.BS3_NaiveMCTS;
import ai.mcts.informedmcts.InformedNaiveMCTS;
import ai.mcts.mlps.MLPSMCTS;
import ai.mcts.naivemcts.NaiveMCTS;
import ai.mcts.naivemcts.TwoPhaseNaiveMCTS;
import ai.mcts.uct.UCTFirstPlayUrgency;
import ai.minimax.RTMiniMax.IDRTMinimax;
import ai.montecarlo.MonteCarlo;
import ai.scv.SCV;
import ai.*;
import ai.CMAB.ScriptsAbstractions.RangedRushPlan;
import ai.abstraction.EconomyMilitaryRush;
import ai.abstraction.HeavyDefense;
import ai.abstraction.HeavyRush;
import ai.abstraction.LightDefense;
import ai.abstraction.LightRush;
import ai.abstraction.RangedDefense;
import ai.abstraction.RangedRush;
import ai.abstraction.WorkerRush;
import ai.abstraction.WorkerRushPlusPlus;
import ai.abstraction.pathfinding.BFSPathFinding;
import ai.ahtn.AHTNAI;
import gui.PhysicalGameStatePanel;
import myAgent.MyAgent;
import myAgent.MyAgentV2;
import mayariBot.mayari;

import javax.swing.JFrame;

import GNS.EconomyLightRush;
import rts.GameState;
import rts.PhysicalGameState;
import rts.PlayerAction;
import rts.units.UnitTypeTable;

/**
 *
 * @author santi
 */
public class GameVisualSimulationTest {
    public static void main(String[] args) throws Exception {
        UnitTypeTable utt = new UnitTypeTable();
        
        // Array con todos los mapas a ejecutar
        String[] maps = {
            // "maps/basesWorkers32x32A.xml",
            // "maps/barricades24x24.xml",
            // //"maps/8x8/FourBasesWorkers8x8.xml",
            // "maps/16x16/TwoBasesBarracks16x16.xml",
            // //"maps/NoWhereToRun9x8.xml",
            // "maps/chambers32x32.xml",
            // "maps/GardenOfWar64x64.xml"
            //"maps/16x16/basesWorkers16x16A.xml",
            //"maps/BWDistantResources32x32.xml",
            "maps/DoubleGame24x24.xml",
            "maps/BroodWar/(2)Benzene.scxA.xml",
            "maps/BroodWar/(2)Destination.scxA.xml",
        };
        
        // Declaración de las IAs fuera del bucle (se crean una sola vez)
        // AI ai1 = new MyAgent(utt);
        // AI ai1 = new MyAgent(utt, 0.2, 0.95, 0.9, 3, 2, 0.3, 0.4, 0.3, 0.08, 0.1);
        //AI ai1 = new MyAgent(utt, 0.2, 0.95, 0.9, 3, 2, 0.3, 0.4, 0.3, 0.08, 0.1);
        //AI ai1 = new MyAgent(utt, 0.5296680302038603, 0.7913396501236944, 0.1484756029295331, 6, 1, 0.6141293126585077, 0.7893003170753544, 0.27548353980645435, 0.1367370822796239, 0.32084294928487345);
        AI ai1 = new MyAgent(utt, 0.9609987620355505, 0.20610609964580984, 0.507066433589285, 4, 4, 0.9707413947048525, 0.3705438550855966, 0.19917051121690899, 0.18188515852994291, 0.1173103447579249
);
        // Array de IAs oponentes
        AI[] opponents = {
            //new mayari(utt)
            //new MyAgent(utt, 0.4859717980626773, 0.6061377722530442, 0.7690359014217759, 5, 2, 0.5359423083410759, 0.2502058625939866, 0.21263002112864848, 0.9258892735541014, 0.8120464407808758),
            //new MyAgent(utt, 0.18243372802157765, 0.018896528679374525, 0.8960905257877619, 5, 11, 0.9502573366218408, 0.608636223992721, 0.3560660179061693, 0.3398173646106416, 0.2635904919086409),
            new MyAgent(utt, 0.3390729325360927, 0.1305158934195393, 0.06912474831286741, 8, 2, 0.7841551494600603, 0.8182534032606329, 0.7844896246021426, 0.4211679057584541, 0.7454018349476341),
            //new WorkerRush(utt),
            //new LightRush(utt),
            // new RangedRush(utt),
            // new HeavyRush(utt),
            // new EconomyMilitaryRush(utt)
            // new WorkerRushPlusPlus(utt),
            // new EconomyLightRush(utt),
            // new HeavyDefense(utt),
            // new LightDefense(utt),
            // new RangedDefense(utt),
            // new RangedRushPlan(utt),
            // new NaiveMCTS(utt),
            // new TwoPhaseNaiveMCTS(utt),
            // new MonteCarlo(utt),
            // new BS3_NaiveMCTS(utt),
            // new SCV(utt),
            // new InformedNaiveMCTS(utt), // no se puede probar, falla
            // new IDRTMinimax(utt),
            // new AHTNAI(utt), // también falla
            // new MLPSMCTS(utt),
            // new UCTFirstPlayUrgency(utt)
        };
        
        // Variables para estadísticas expandidas
        long startTime = System.currentTimeMillis();
        String ai1Name = ai1.getClass().getSimpleName();
        
        // Estadísticas por oponente
        int[] ai1WinsVsOpponent = new int[opponents.length];
        int[] opponentWins = new int[opponents.length];
        int[] drawsVsOpponent = new int[opponents.length];
        int[] ai1WinsAsPlayer0VsOpponent = new int[opponents.length];
        int[] ai1WinsAsPlayer1VsOpponent = new int[opponents.length];
        int[] opponentWinsAsPlayer0 = new int[opponents.length];
        int[] opponentWinsAsPlayer1 = new int[opponents.length];
        
        // Estadísticas totales
        int totalAi1Wins = 0, totalOpponentWins = 0, totalDraws = 0;
        
        
        // Loop principal: por cada oponente, ejecutar en ambas configuraciones
        for (int opponentIndex = 0; opponentIndex < opponents.length; opponentIndex++) {
            AI currentOpponent = opponents[opponentIndex];
            String opponentName = currentOpponent.getClass().getSimpleName();
            
            System.out.println("\n" + "=".repeat(80));
            System.out.println("         ENFRENTAMIENTO: " + ai1Name + " vs " + opponentName);
            System.out.println("=".repeat(80));
            
            // Dos rondas por cada oponente: ai1 vs opponent, luego opponent vs ai1
            for (int round = 0; round < 2; round++) {
                if (round == 0) {
                    System.out.println("=== RONDA 1: " + ai1Name + " vs " + opponentName + " ===");
                } else {
                    System.out.println("=== RONDA 2: " + opponentName + " vs " + ai1Name + " (IAs intercambiadas) ===");
                }
                
                for (int mapIndex = 0; mapIndex < maps.length; mapIndex++) {
                    System.out.println("Ejecutando mapa " + (mapIndex + 1) + "/" + maps.length + ": " + maps[mapIndex]);
                    
                    PhysicalGameState pgs = PhysicalGameState.load(maps[mapIndex], utt);
                    GameState gs = new GameState(pgs, utt);
                    int MAXCYCLES = 5000;
                    int PERIOD = 20;
                    boolean gameover = false;

                    JFrame w = PhysicalGameStatePanel.newVisualizer(gs, 640, 640, false, PhysicalGameStatePanel.COLORSCHEME_BLACK);

                    long nextTimeToUpdate = System.currentTimeMillis() + PERIOD;
                    do {
                        if (System.currentTimeMillis() >= nextTimeToUpdate) {
                            PlayerAction pa1, pa2;
                            
                            // En la primera ronda: ai1 es jugador 0, opponent es jugador 1
                            // En la segunda ronda: opponent es jugador 0, ai1 es jugador 1
                            if (round == 0) {
                                pa1 = ai1.getAction(0, gs);
                                pa2 = currentOpponent.getAction(1, gs);
                            } else {
                                pa1 = currentOpponent.getAction(0, gs);
                                pa2 = ai1.getAction(1, gs);
                            }
                            
                            gs.issueSafe(pa1);
                            gs.issueSafe(pa2);

                            // simulate:
                            gameover = gs.cycle();
                            w.repaint();
                            nextTimeToUpdate += PERIOD;
                        } else {
                            try {
                                Thread.sleep(1);
                            } catch (Exception e) {
                                e.printStackTrace();
                            }
                        }
                    } while (!gameover && gs.getTime() < MAXCYCLES);
                    
                    // Notificar a las IAs que el juego terminó
                    if (round == 0) {
                        ai1.gameOver(gs.winner());
                        currentOpponent.gameOver(gs.winner());
                    } else {
                        currentOpponent.gameOver(gs.winner());
                        ai1.gameOver(gs.winner());
                    }

                    // Mostrar resultado y actualizar estadísticas
                    String player0Name = (round == 0) ? ai1Name : opponentName;
                    String player1Name = (round == 0) ? opponentName : ai1Name;
                    
                    // Actualizar estadísticas
                    int winner = gs.winner();
                    if (winner == -1) {
                        drawsVsOpponent[opponentIndex]++;
                        totalDraws++;
                    } else if (round == 0) {
                        // Ronda 1: ai1 es player0, opponent es player1
                        if (winner == 0) {
                            ai1WinsVsOpponent[opponentIndex]++;
                            ai1WinsAsPlayer0VsOpponent[opponentIndex]++;
                            totalAi1Wins++;
                        } else {
                            opponentWins[opponentIndex]++;
                            opponentWinsAsPlayer1[opponentIndex]++;
                            totalOpponentWins++;
                        }
                    } else {
                        // Ronda 2: opponent es player0, ai1 es player1
                        if (winner == 0) {
                            opponentWins[opponentIndex]++;
                            opponentWinsAsPlayer0[opponentIndex]++;
                            totalOpponentWins++;
                        } else {
                            ai1WinsVsOpponent[opponentIndex]++;
                            ai1WinsAsPlayer1VsOpponent[opponentIndex]++;
                            totalAi1Wins++;
                        }
                    }
                    
                    System.out.println("Mapa " + maps[mapIndex] + " completado.");
                    System.out.println("Jugador 0 (" + player0Name + ") vs Jugador 1 (" + player1Name + ")");
                    System.out.println("Ganador: " + (winner == 0 ? player0Name : winner == 1 ? player1Name : "Empate"));
                    System.out.println("---------------------------------------------------------------");
                    
                    // Cerrar la ventana del visualizador antes de continuar con el siguiente mapa
                    w.dispose();
                    
                    // Pausa opcional entre mapas
                    try {
                        Thread.sleep(1000); // 1 segundo de pausa entre mapas
                    } catch (InterruptedException e) {
                        e.printStackTrace();
                    }
                }
                
                System.out.println("=== FIN DE LA RONDA " + (round + 1) + " contra " + opponentName + " ===");
                System.out.println();
            }
            
            // Resumen del enfrentamiento contra este oponente
            int totalGamesVsOpponent = ai1WinsVsOpponent[opponentIndex] + opponentWins[opponentIndex] + drawsVsOpponent[opponentIndex];
            System.out.println("🎯 RESUMEN vs " + opponentName + ":");
            System.out.printf("   %s: %d/%d victorias (%.1f%%)\n", ai1Name, ai1WinsVsOpponent[opponentIndex], totalGamesVsOpponent, 
                             (ai1WinsVsOpponent[opponentIndex] * 100.0 / totalGamesVsOpponent));
            System.out.printf("   %s: %d/%d victorias (%.1f%%)\n", opponentName, opponentWins[opponentIndex], totalGamesVsOpponent, 
                             (opponentWins[opponentIndex] * 100.0 / totalGamesVsOpponent));
            System.out.printf("   Empates: %d/%d (%.1f%%)\n", drawsVsOpponent[opponentIndex], totalGamesVsOpponent, 
                             (drawsVsOpponent[opponentIndex] * 100.0 / totalGamesVsOpponent));
            System.out.println();
        }
        
        System.out.println("Todos los enfrentamientos han sido completados.");
        
        // ========== RESUMEN DE ESTADÍSTICAS ==========
        System.out.println("\n" + "=".repeat(80));
        System.out.println("                    RESUMEN GENERAL DE ESTADÍSTICAS");
        System.out.println("=".repeat(80));
        
        int totalGames = totalAi1Wins + totalOpponentWins + totalDraws;
        System.out.println("Total de partidas jugadas: " + totalGames);
        System.out.println("Total de mapas por oponente: " + maps.length);
        System.out.println("Número de oponentes: " + opponents.length);
        System.out.println("Rondas por oponente: 2");
        System.out.println();
        
        // Estadísticas generales
        System.out.println("RESULTADOS GENERALES:");
        System.out.printf("%-20s: %3d victorias (%.1f%%)\n", ai1Name, totalAi1Wins, (totalAi1Wins * 100.0 / totalGames));
        System.out.printf("%-20s: %3d victorias (%.1f%%)\n", "Todos los oponentes", totalOpponentWins, (totalOpponentWins * 100.0 / totalGames));
        System.out.printf("%-20s: %3d empates   (%.1f%%)\n", "Empates", totalDraws, (totalDraws * 100.0 / totalGames));
        System.out.println();
        
        // Estadísticas detalladas por oponente
        System.out.println("RESULTADOS DETALLADOS POR OPONENTE:");
        System.out.println("-".repeat(80));
        for (int i = 0; i < opponents.length; i++) {
            String opponentName = opponents[i].getClass().getSimpleName();
            int gamesVsOpponent = ai1WinsVsOpponent[i] + opponentWins[i] + drawsVsOpponent[i];
            
            System.out.printf("🎯 %s vs %s:\n", ai1Name, opponentName);
            System.out.printf("   %s: %2d/%2d victorias (%.1f%%) | Como P0: %d | Como P1: %d\n", 
                             ai1Name, ai1WinsVsOpponent[i], gamesVsOpponent, 
                             (ai1WinsVsOpponent[i] * 100.0 / gamesVsOpponent),
                             ai1WinsAsPlayer0VsOpponent[i], ai1WinsAsPlayer1VsOpponent[i]);
            System.out.printf("   %s: %2d/%2d victorias (%.1f%%) | Como P0: %d | Como P1: %d\n", 
                             opponentName, opponentWins[i], gamesVsOpponent, 
                             (opponentWins[i] * 100.0 / gamesVsOpponent),
                             opponentWinsAsPlayer0[i], opponentWinsAsPlayer1[i]);
            System.out.printf("   Empates: %2d/%2d (%.1f%%)\n", 
                             drawsVsOpponent[i], gamesVsOpponent, 
                             (drawsVsOpponent[i] * 100.0 / gamesVsOpponent));
            
            // Mostrar resultado individual
            if (ai1WinsVsOpponent[i] > opponentWins[i]) {
                int diff = ai1WinsVsOpponent[i] - opponentWins[i];
                System.out.printf("   🏆 %s domina (+%d victoria%s)\n", ai1Name, diff, diff > 1 ? "s" : "");
            } else if (opponentWins[i] > ai1WinsVsOpponent[i]) {
                int diff = opponentWins[i] - ai1WinsVsOpponent[i];
                System.out.printf("   🏆 %s domina (+%d victoria%s)\n", opponentName, diff, diff > 1 ? "s" : "");
            } else {
                System.out.printf("   🤝 Enfrentamiento equilibrado\n");
            }
            System.out.println();
        }
        
        // Análisis competitivo general
        System.out.println("ANÁLISIS COMPETITIVO GENERAL:");
        System.out.println("-".repeat(50));
        if (totalAi1Wins > totalOpponentWins) {
            int diff = totalAi1Wins - totalOpponentWins;
            double advantage = ((double) totalAi1Wins / totalGames) * 100.0;
            System.out.println("🏆 " + ai1Name + " es SUPERIOR globalmente");
            System.out.printf("   Ventaja: +%d victorias | Tasa de éxito: %.1f%%\n", diff, advantage);
            
            // Contar victorias contra cada oponente
            int opponentsBeaten = 0;
            for (int i = 0; i < opponents.length; i++) {
                if (ai1WinsVsOpponent[i] > opponentWins[i]) {
                    opponentsBeaten++;
                }
            }
            System.out.printf("   Domina a %d/%d oponentes\n", opponentsBeaten, opponents.length);
            
        } else if (totalOpponentWins > totalAi1Wins) {
            int diff = totalOpponentWins - totalAi1Wins;
            double disadvantage = ((double) totalOpponentWins / totalGames) * 100.0;
            System.out.println("📉 " + ai1Name + " necesita mejoras");
            System.out.printf("   Desventaja: -%d victorias | Los oponentes ganan %.1f%% del tiempo\n", diff, disadvantage);
        } else {
            System.out.println("🤝 " + ai1Name + " está perfectamente equilibrado con el conjunto de oponentes");
        }
        
        // Análisis posicional
        System.out.println();
        System.out.println("ANÁLISIS POR POSICIÓN INICIAL:");
        System.out.println("-".repeat(50));
        int totalPlayer0Wins = 0, totalPlayer1Wins = 0;
        for (int i = 0; i < opponents.length; i++) {
            totalPlayer0Wins += ai1WinsAsPlayer0VsOpponent[i] + opponentWinsAsPlayer0[i];
            totalPlayer1Wins += ai1WinsAsPlayer1VsOpponent[i] + opponentWinsAsPlayer1[i];
        }
        
        int totalPositionalGames = totalPlayer0Wins + totalPlayer1Wins;
        System.out.printf("Jugador 0: %3d victorias (%.1f%%)\n", totalPlayer0Wins, (totalPlayer0Wins * 100.0 / totalPositionalGames));
        System.out.printf("Jugador 1: %3d victorias (%.1f%%)\n", totalPlayer1Wins, (totalPlayer1Wins * 100.0 / totalPositionalGames));
        
        if (Math.abs(totalPlayer0Wins - totalPlayer1Wins) <= 2) {
            System.out.println("📍 No hay ventaja significativa por posición inicial");
        } else if (totalPlayer0Wins > totalPlayer1Wins) {
            System.out.println("📍 Existe ventaja para el Jugador 0 (posición inicial)");
        } else {
            System.out.println("📍 Existe ventaja para el Jugador 1");
        }
        
        // Tiempo total empleado
        long endTime = System.currentTimeMillis();
        long totalTimeMs = endTime - startTime;
        double totalTimeSeconds = totalTimeMs / 1000.0;
        int minutes = (int) (totalTimeSeconds / 60);
        double seconds = totalTimeSeconds % 60;
        
        System.out.println();
        System.out.println("TIEMPO DE EJECUCIÓN:");
        System.out.println("-".repeat(30));
        if (minutes > 0) {
            System.out.printf("⏱️  Tiempo total: %d minutos %.1f segundos (%.1f segundos totales)\n", 
                             minutes, seconds, totalTimeSeconds);
        } else {
            System.out.printf("⏱️  Tiempo total: %.1f segundos\n", totalTimeSeconds);
        }
        System.out.printf("📊 Tiempo promedio por partida: %.1f segundos\n", totalTimeSeconds / totalGames);
        System.out.printf("🎯 Tiempo promedio por oponente: %.1f segundos\n", totalTimeSeconds / opponents.length);
        System.out.printf("🗺️  Tiempo promedio por mapa: %.1f segundos\n", totalTimeSeconds / (maps.length * opponents.length * 2));
        
        System.out.println("=".repeat(80));
    }
}
