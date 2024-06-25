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
        PhysicalGameState pgs;
        // pgs = PhysicalGameState.load("maps/4x4/base4x4.xml", utt);
        // pgs = PhysicalGameState.load("maps/8x8/bases8x8.xml", utt);
        // pgs = PhysicalGameState.load("maps/16x16/basesWorkers16x16.xml", utt);
        // pgs = PhysicalGameState.load("maps/24x24/basesWorkers24x24.xml", utt);
        // pgs = PhysicalGameState.load("maps/GardenOfWar64x64.xml", utt);
        // pgs = PhysicalGameState.load("maps/chambers32x32.xml", utt);
        // pgs = PhysicalGameState.load("maps/chambers32x32.xml", utt);
        // PhysicalGameState pgs = MapGenerator.basesWorkers8x8Obstacle();

        /* MAPAS COMPETICIÓN (SON 12) */
        // pgs = PhysicalGameState.load("maps/melee14x12Mixed18.xml", utt);
        // pgs = PhysicalGameState.load("maps/16x16/basesWorkers16x16A.xml", utt);
        // pgs = PhysicalGameState.load("maps/basesWorkers32x32A.xml", utt);
        // pgs = PhysicalGameState.load("maps/barricades24x24.xml", utt);
        // pgs = PhysicalGameState.load("maps/8x8/FourBasesWorkers8x8.xml", utt);
        // pgs = PhysicalGameState.load("maps/16x16/TwoBasesBarracks16x16.xml", utt);
        // pgs = PhysicalGameState.load("maps/NoWhereToRun9x8.xml", utt);
        // pgs = PhysicalGameState.load("maps/chambers32x32.xml", utt);
        // pgs = PhysicalGameState.load("maps/GardenOfWar64x64.xml", utt);
        // pgs = PhysicalGameState.load("maps/BroodWar/(2)Benzene.scxA.xml", utt);
        pgs = PhysicalGameState.load("maps/BroodWar/(2)Destination.scxA.xml", utt);
        // pgs = PhysicalGameState.load("maps/BroodWar/(4)Andromeda.scxB.xml", utt);

        GameState gs = new GameState(pgs, utt);
        int MAXCYCLES = 10000;
        int PERIOD = 20;
        boolean gameover = false;

        AI ai1 = new MyAgent(utt);
        // AI ai1 = new MyAgent(utt, 0.2, 0.95, 0.9, 3, 0, 0.3, 0.4, 0.3, 0.08, 0.1);
        // AI ai1 = new WorkerRush(utt);
        // AI ai1 = new WorkerRush(utt);
        // AI ai1 = new EconomyMilitaryRush(utt);
        AI ai2;
        ai2 = new RandomBiasedAI();
        // ai2 = new WorkerRushPlusPlus(utt);
        // ai2 = new WorkerRush(utt);
        // ai2 = new RangedRush(utt);
        // ai2 = new HeavyRush(utt);
        // ai2 = new LightRush(utt);
        // ai2 = new EconomyMilitaryRush(utt);
        // ai2 = new EconomyLightRush(utt);
        // ai2 = new HeavyDefense(utt);
        // ai2 = new LightDefense(utt);
        // ai2 = new RangedDefense(utt);
        // ai2 = new RangedRushPlan(utt);
        // ai2 = new NaiveMCTS(utt);
        // ai2 = new TwoPhaseNaiveMCTS(utt);
        // ai2 = new MonteCarlo(utt);
        // ai2 = new BS3_NaiveMCTS(utt);
        // ai2 = new SCV(utt);
        // ai2 = new InformedNaiveMCTS(utt); // no se puede probar, falla
        // ai2 = new IDRTMinimax(utt);
        // ai2 = new AHTNAI(utt); // también falla
        // ai2 = new MLPSMCTS(utt);
        // ai2 = new UCTFirstPlayUrgency(utt);

        JFrame w = PhysicalGameStatePanel.newVisualizer(gs, 640, 640, false, PhysicalGameStatePanel.COLORSCHEME_BLACK);
        // JFrame w =
        // PhysicalGameStatePanel.newVisualizer(gs,640,640,false,PhysicalGameStatePanel.COLORSCHEME_WHITE);

        long nextTimeToUpdate = System.currentTimeMillis() + PERIOD;
        do {
            if (System.currentTimeMillis() >= nextTimeToUpdate) {
                PlayerAction pa1 = ai1.getAction(0, gs);
                PlayerAction pa2 = ai2.getAction(1, gs);
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
        ai1.gameOver(gs.winner());
        ai2.gameOver(gs.winner());

        System.out.println("Game Over");
    }
}
